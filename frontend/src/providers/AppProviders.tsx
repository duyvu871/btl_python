import {MantineProvider} from '@mantine/core';
import {Notifications} from '@mantine/notifications';
import {QueryClientProvider} from '@tanstack/react-query';
import {Provider as JotaiProvider} from 'jotai';
import React from 'react';
import {ReactQueryDevtools} from '@tanstack/react-query-devtools';
import {QueryClient} from '@tanstack/react-query';
import {AuthProvider} from './AuthProvider';

interface AppProvidersProps {
    children: React.ReactNode;
}

export function AppProviders({children}: AppProvidersProps) {

    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: 1,
                refetchOnWindowFocus: false,
                staleTime: 5 * 60 * 1000, // 5 minutes
            },
            mutations: {
                retry: 0,
            },
        },
    });


    return (
        <QueryClientProvider client={queryClient}>
            <MantineProvider defaultColorScheme="dark">
                <Notifications/>
                <JotaiProvider>
                    <AuthProvider>
                        {children}
                    </AuthProvider>
                </JotaiProvider>
                <ReactQueryDevtools initialIsOpen={false}/>
            </MantineProvider>
        </QueryClientProvider>
    );
}
