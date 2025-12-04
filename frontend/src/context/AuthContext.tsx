import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthResponse, AuthState } from '../types/auth';
import { apiClient } from '../services/api';

interface AuthContextType extends AuthState {
    login: (token: string, user: User) => void;
    logout: () => void;
    updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [state, setState] = useState<AuthState>({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: true,
    });

    useEffect(() => {
        // Load from localStorage on mount
        const token = localStorage.getItem('auth_token');
        const userStr = localStorage.getItem('auth_user');

        if (token && userStr) {
            try {
                const user = JSON.parse(userStr);
                setState({
                    user,
                    token,
                    isAuthenticated: true,
                    isLoading: false,
                });

                // Set default header
                apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            } catch (e) {
                // Invalid data
                logout();
            }
        } else {
            setState(prev => ({ ...prev, isLoading: false }));
        }
    }, []);

    const login = (token: string, user: User) => {
        localStorage.setItem('auth_token', token);
        localStorage.setItem('auth_user', JSON.stringify(user));

        apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;

        setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
        });
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');

        delete apiClient.defaults.headers.common['Authorization'];

        setState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
        });
    };

    const updateUser = (user: User) => {
        localStorage.setItem('auth_user', JSON.stringify(user));
        setState(prev => ({ ...prev, user }));
    };

    return (
        <AuthContext.Provider value={{ ...state, login, logout, updateUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
