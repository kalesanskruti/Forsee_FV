import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// --- TYPE DEFINITIONS ---

export type UserRole = 'admin' | 'engineer' | 'viewer' | null;

export interface User {
    id: string;
    name: string;
    email: string;
    avatarUrl?: string;
}

interface AuthContextType {
    user: User | null;
    userRole: UserRole;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    signup: (name: string, email: string, password: string) => Promise<void>;
    loginWithGoogle: () => Promise<void>;
    logout: () => void;
    setRole: (role: UserRole) => void;
}

// --- CONTEXT ---

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// --- PROVIDER ---

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [userRole, setUserRole] = useState<UserRole>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        const storedUser = localStorage.getItem('forsee_user');
        const storedRole = localStorage.getItem('forsee_role') as UserRole;

        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
                if (storedRole) {
                    setUserRole(storedRole);
                }
            } catch {
                localStorage.removeItem('forsee_user');
                localStorage.removeItem('forsee_role');
            }
        }
        setIsLoading(false);
    }, []);

    const setRole = (role: UserRole) => {
        setUserRole(role);
        if (role) {
            localStorage.setItem('forsee_role', role);
        } else {
            localStorage.removeItem('forsee_role');
        }
    };

    const login = async (email: string, password: string) => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));

        // For demo: accept any email/password
        const newUser: User = {
            id: crypto.randomUUID(),
            name: email.split('@')[0],
            email,
            avatarUrl: '/avatar.png',
        };

        setUser(newUser);
        localStorage.setItem('forsee_user', JSON.stringify(newUser));
        // Reset role on new login so they get the popup
        setRole(null);
    };

    const signup = async (name: string, email: string, password: string) => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));

        const newUser: User = {
            id: crypto.randomUUID(),
            name,
            email,
            avatarUrl: '/avatar.png',
        };

        setUser(newUser);
        localStorage.setItem('forsee_user', JSON.stringify(newUser));
        // Reset role on new signup
        setRole(null);
    };

    const loginWithGoogle = async () => {
        // Simulate Google OAuth
        await new Promise(resolve => setTimeout(resolve, 500));

        const newUser: User = {
            id: crypto.randomUUID(),
            name: 'Demo User',
            email: 'demo@forsee.ai',
            avatarUrl: '/avatar.png',
        };

        setUser(newUser);
        localStorage.setItem('forsee_user', JSON.stringify(newUser));
        // Reset role on new login
        setRole(null);
    };

    const logout = () => {
        setUser(null);
        setRole(null);
        localStorage.removeItem('forsee_user');
        localStorage.removeItem('forsee_role');
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                userRole,
                isAuthenticated: !!user,
                isLoading,
                login,
                signup,
                loginWithGoogle,
                logout,
                setRole,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

// --- HOOK ---

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthProvider;
