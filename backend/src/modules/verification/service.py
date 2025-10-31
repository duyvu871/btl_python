"""
Verification Service for generating and verifying one-time codes.
Supports email use_cases, password reset, and other use_cases flows.
"""

import secrets
import time
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends
from redis.asyncio import Redis

from src.core.redis.client import get_redis


@dataclass
class VerificationOptions:
    """Options for generating/verifying codes."""

    namespace: str  # "email-verify" | "password-reset" | ...
    subject: str  # email or userId
    ttl_sec: int = 600  # default 10 minutes
    max_attempts: int = 5  # maximum number of incorrect attempts
    length: int = 6  # code length, default 6
    rate_limit_window_sec: int = 60  # time to block resending
    rate_limit_max: int = 3  # maximum number of codes in the window


@dataclass
class GenerateResult:
    """Result from generating a use_cases code."""

    code: str  # returned for you to send email/SMS
    expires_at: int  # epoch milliseconds


class VerificationService:
    """
    Service for generating and verifying one-time codes with rate limiting.

    Features:
    - Generate random numeric codes
    - Store hashed codes in Redis (Argon2)
    - Rate limiting to prevent spam
    - Attempt tracking to prevent brute force
    - One-time use codes (consume after use_cases)

    Example:
        service = VerificationService(redis_client)

        # Generate code
        result = await service.generate(VerificationOptions(
            namespace="email-verify",
            subject="user@example.com"
        ))
        # Send result.code via email

        # Verify code
        valid = await service.verify_and_consume(VerificationOptions(
            namespace="email-verify",
            subject="user@example.com"
        ), code="123456")
    """

    def __init__(self, redis: Redis):
        """
        Initialize use_cases service.

        Args:
            redis: Async Redis client instance
        """
        self.redis = redis
        self.ph = PasswordHasher()

    def _key_code(self, ns: str, subject: str) -> str:
        """Generate Redis key for code hash."""
        return f"verify:{ns}:{subject}:code"

    def _key_attempts(self, ns: str, subject: str) -> str:
        """Generate Redis key for attempts counter."""
        return f"verify:{ns}:{subject}:attempts"

    def _key_rate(self, ns: str, subject: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"verify:{ns}:{subject}:rate"

    def _random_numeric(self, length: int) -> str:
        """
        Generate a random numeric code.

        Args:
            length: Length of the code

        Returns:
            Random numeric string
        """
        # Use secrets for cryptographically strong randomness
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    async def generate(self, opts: VerificationOptions) -> GenerateResult:
        """
        Generate a use_cases code and store it in Redis.

        Args:
            opts: Verification options

        Returns:
            GenerateResult with code and expiration

        Raises:
            Exception: If rate limit is exceeded
        """
        # Rate limiting: increment counter in the window
        rate_key = self._key_rate(opts.namespace, opts.subject)

        # Use pipeline for atomic operations
        async with self.redis.pipeline() as pipe:
            await pipe.incr(rate_key)
            await pipe.ttl(rate_key)
            results = await pipe.execute()

        current = results[0]
        ttl = results[1]

        # Set expiration on first increment
        if ttl == -1:
            await self.redis.expire(rate_key, opts.rate_limit_window_sec)

        # Check rate limit
        if current > opts.rate_limit_max:
            raise Exception("Too many requests. Please try again later.")

        # Generate code and hash it
        code = self._random_numeric(opts.length)
        code_hash = self.ph.hash(code)

        code_key = self._key_code(opts.namespace, opts.subject)
        attempts_key = self._key_attempts(opts.namespace, opts.subject)

        # Save hash + attempts with TTL (use pipeline for consistency)
        async with self.redis.pipeline() as pipe:
            await pipe.setex(code_key, opts.ttl_sec, code_hash)
            await pipe.setex(attempts_key, opts.ttl_sec, str(opts.max_attempts))
            await pipe.execute()

        expires_at = int((time.time() + opts.ttl_sec) * 1000)  # milliseconds

        return GenerateResult(code=code, expires_at=expires_at)

    async def verify(self, opts: VerificationOptions, code: str) -> bool:
        """
        Verify a code without consuming it.

        Args:
            opts: Verification options
            code: Code to verify

        Returns:
            True if code is valid, False otherwise
        """
        code_key = self._key_code(opts.namespace, opts.subject)
        attempts_key = self._key_attempts(opts.namespace, opts.subject)

        # Get hash and attempts
        code_hash, attempts_str = await self.redis.mget([code_key, attempts_key])

        if not code_hash:
            return False

        # Decode bytes to string if needed
        if isinstance(code_hash, bytes):
            code_hash = code_hash.decode("utf-8")
        if isinstance(attempts_str, bytes):
            attempts_str = attempts_str.decode("utf-8")

        # Check attempts
        try:
            attempts = int(attempts_str) if attempts_str else 0
        except (ValueError, TypeError):
            attempts = 0

        if attempts <= 0:
            return False

        # Verify code
        try:
            self.ph.verify(code_hash, code)
            return True
        except (VerifyMismatchError, InvalidHashError):
            # Decrease attempts
            await self.redis.decr(attempts_key)
            return False

    async def consume(self, namespace: str, subject: str) -> None:
        """
        Consume a code (delete it for one-time use).

        Args:
            namespace: Verification namespace
            subject: Subject (email, userId, etc.)
        """
        code_key = self._key_code(namespace, subject)
        attempts_key = self._key_attempts(namespace, subject)
        await self.redis.delete(code_key, attempts_key)

    async def verify_and_consume(self, opts: VerificationOptions, code: str) -> bool:
        """
        Verify a code and consume it if valid.

        Args:
            opts: Verification options
            code: Code to verify

        Returns:
            True if code is valid and consumed, False otherwise
        """
        is_valid = await self.verify(opts, code)
        if is_valid:
            await self.consume(opts.namespace, opts.subject)
        return is_valid

    async def get_remaining_attempts(self, namespace: str, subject: str) -> int | None:
        """
        Get remaining use_cases attempts.

        Args:
            namespace: Verification namespace
            subject: Subject (email, userId, etc.)

        Returns:
            Number of remaining attempts, or None if no code exists
        """
        attempts_key = self._key_attempts(namespace, subject)
        attempts_str = await self.redis.get(attempts_key)

        if not attempts_str:
            return None

        if isinstance(attempts_str, bytes):
            attempts_str = attempts_str.decode("utf-8")

        try:
            return int(attempts_str)
        except (ValueError, TypeError):
            return None


# Dependency for FastAPI
async def get_verification_service(redis=Depends(get_redis)) -> VerificationService:
    """
    Get use_cases service instance (FastAPI dependency).

    Returns:
        VerificationService instance with Redis connection
    """
    return VerificationService(redis)
