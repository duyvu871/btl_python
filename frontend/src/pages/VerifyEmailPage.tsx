import {useState, useEffect, useCallback, useRef} from 'react';
import {useNavigate, useSearchParams} from 'react-router-dom';
import {
    Container,
    Paper,
    Title,
    Text,
    PinInput,
    Button,
    Stack,
    Group,
    Alert,
} from '@mantine/core';
import {IconCheck, IconX, IconMail} from '@tabler/icons-react';
import {useVerifyEmail, useResendVerification} from '@/hooks/useVerification';
import { ApiError } from '@/api/base';

export function VerifyEmailPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const email = searchParams.get('email') || '';
    const codeFromUrl = searchParams.get('code') || '';

    const [code, setCode] = useState(codeFromUrl);
    const [showVerifyAlerts, setShowVerifyAlerts] = useState(true);

    const verifyMutation = useVerifyEmail();
    const resendMutation = useResendVerification();

    const autoSubmittedRef = useRef(false);

    // Hide verify alerts when resend mutation state changes
    useEffect(() => {
        if (resendMutation.isError || resendMutation.isSuccess) {
            setShowVerifyAlerts(false);
        }
    }, [resendMutation.isError, resendMutation.isSuccess]);

    const handleVerify = useCallback(async () => {
        if (code.length !== 6) return;

        try {
            await verifyMutation.mutateAsync({
                email,
                code,
            });
        } catch (error) {
            console.error('Verification failed:', error);
        }
    }, [code, email, verifyMutation]);

    // Auto-submit if code is provided in URL (from email click)
    useEffect(() => {
        if (autoSubmittedRef.current) return;
        if (codeFromUrl && codeFromUrl.length === 6 && email) {
            autoSubmittedRef.current = true;
            verifyMutation
                .mutateAsync({email, code: codeFromUrl})
                .catch((err) => {
                    console.error('Verification failed (auto):', err);
                });
        }
    }, [codeFromUrl, email, verifyMutation]);

    const handleResend = async () => {
        try {
            setShowVerifyAlerts(false); // Hide verify alerts before resending
            await resendMutation.mutateAsync({email});
            setCode(''); // Clear the input
        } catch (error) {
            console.error('Resend failed:', error);
        }
    };

    const isLoading = verifyMutation.isPending;
    const isResending = resendMutation.isPending;

    return (
        <Container size="xs" style={{width: '100%', maxWidth: 420, minHeight: "100vh", display: 'flex', alignItems: 'center' }}>
            <Paper shadow="md" p="xl" radius="md" withBorder w={"100%"}>
                <Stack gap="lg">
                    <div style={{textAlign: 'center'}}>
                        <IconMail size={48} style={{margin: '0 auto'}}/>
                        <Title order={2} mt="md">Verify Your Email</Title>
                        <Text c="dimmed" size="sm" mt="xs">
                            We sent a verification code to
                        </Text>
                        <Text fw={600} size="sm">
                            {email}
                        </Text>
                    </div>

                    {showVerifyAlerts && verifyMutation.isSuccess && (
                        <Alert icon={<IconCheck size={16}/>} color="green" title="Success!">
                            Email verified successfully! You can now log in.
                        </Alert>
                    )}

                    {showVerifyAlerts && verifyMutation.isError && (
                        <Alert icon={<IconX size={16}/>} color="red" title="Verification Failed">
                            {verifyMutation.error instanceof ApiError
                                ? verifyMutation.error.message
                                : 'Invalid or expired code. Please try again.'}
                        </Alert>
                    )}

                    {resendMutation.isSuccess && (
                        <Alert icon={<IconCheck size={16}/>} color="blue" title="Code Sent">
                            A new verification code has been sent to your email.
                        </Alert>
                    )}

                    {resendMutation.isError && (
                        <Alert icon={<IconX size={16}/>} color="red" title="Failed to Send">
                            {resendMutation.error instanceof ApiError
                                ? resendMutation.error.message
                                : 'Failed to resend verification code.'}
                        </Alert>
                    )}

                    {/* Hiển thị nút Go to Login khi verify thành công */}
                    {verifyMutation.isSuccess && (
                        <Button
                            fullWidth
                            size="md"
                            variant="filled"
                            color="green"
                            onClick={() => navigate('/login')}
                        >
                            Go to Login
                        </Button>
                    )}

                    {/* Chỉ hiển thị form verify khi chưa success */}
                    {!verifyMutation.isSuccess && (
                        <>
                            <Stack gap="md" align="center">
                                <Text size="sm" c="dimmed">
                                    Enter the 6-digit code
                                </Text>
                                <PinInput
                                    length={6}
                                    value={code}
                                    onChange={(value) => {
                                        setCode(value);
                                        if (value.length > 0 && !showVerifyAlerts) {
                                            setShowVerifyAlerts(true);
                                        }
                                    }}
                                    size="lg"
                                    type="number"
                                    disabled={isLoading}
                                    onComplete={handleVerify}
                                />
                            </Stack>

                            <Button
                                fullWidth
                                onClick={handleVerify}
                                disabled={code.length !== 6 || isLoading}
                                loading={isLoading}
                            >
                                {isLoading ? 'Verifying...' : 'Verify Email'}
                            </Button>

                            <Group justify="center" gap="xs">
                                <Text size="sm" c="dimmed">
                                    Didn't receive the code?
                                </Text>
                                <Button
                                    variant="subtle"
                                    size="sm"
                                    onClick={handleResend}
                                    disabled={isResending}
                                    loading={isResending}
                                >
                                    Resend Code
                                </Button>
                            </Group>
                        </>
                    )}
                </Stack>
            </Paper>
        </Container>
    );
}
