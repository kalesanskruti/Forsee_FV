import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth, UserRole } from '@/context/AuthContext';
import { Shield, Wrench, Eye, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNavigate } from 'react-router-dom';

interface RoleCardProps {
    role: UserRole;
    title: string;
    icon: React.ComponentType<{ className?: string }>;
    description: string;
    features: string[];
    onSelect: (role: UserRole) => void;
    isSelected: boolean;
}

const RoleCard = ({ role, title, icon: Icon, description, features, onSelect, isSelected }: RoleCardProps) => (
    <motion.button
        whileHover={{ scale: 1.02, backgroundColor: "rgba(255, 255, 255, 0.03)" }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onSelect(role)}
        className={cn(
            "relative flex flex-col items-start p-6 rounded-xl border transition-all duration-300 w-full text-left group",
            isSelected
                ? "bg-primary/10 border-primary shadow-[0_0_20px_rgba(157,78,221,0.2)]"
                : "bg-white/5 border-white/10 hover:border-white/20"
        )}
    >
        <div className={cn(
            "p-3 rounded-lg mb-4 transition-colors",
            isSelected ? "bg-primary text-white" : "bg-white/10 text-white/70 group-hover:text-white"
        )}>
            <Icon className="w-6 h-6" />
        </div>

        <h3 className={cn("text-lg font-bold mb-2", isSelected ? "text-primary" : "text-white")}>
            {title}
        </h3>

        <p className="text-white/60 text-sm mb-4 leading-relaxed">
            {description}
        </p>

        <ul className="space-y-2 mt-auto">
            {features.map((feature, idx) => (
                <li key={idx} className="flex items-center gap-2 text-xs text-white/50">
                    <Check className="w-3 h-3 text-primary" />
                    {feature}
                </li>
            ))}
        </ul>

        {isSelected && (
            <motion.div
                layoutId="role-check"
                className="absolute top-4 right-4 w-6 h-6 bg-primary rounded-full flex items-center justify-center text-white"
            >
                <Check className="w-4 h-4" />
            </motion.div>
        )}
    </motion.button>
);

export function RoleSelectionModal() {
    const { user, userRole, setRole, isAuthenticated } = useAuth();
    const [selectedRole, setSelectedRole] = useState<UserRole>(null);
    const navigate = useNavigate();

    // Show modal only if user is logged in BUT has no role assigned
    const showModal = isAuthenticated && !userRole;

    const handleConfirm = () => {
        if (selectedRole) {
            setRole(selectedRole);
            // Optional: navigate to a specific start page based on role
            // if (selectedRole === 'admin') navigate('/dashboard');
        }
    };

    if (!showModal) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
            >
                <div className="max-w-4xl w-full bg-[#0a0a0a] border border-white/10 rounded-2xl p-6 md:p-8 shadow-2xl relative overflow-hidden">
                    {/* Background Gradients */}
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[100px] pointer-events-none" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

                    <div className="relative z-10 text-center mb-8">
                        <h2 className="text-3xl font-bold text-white mb-2">Welcome, {user?.name}</h2>
                        <p className="text-white/60">Select your role to access the platform</p>
                    </div>

                    <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                        <RoleCard
                            role="admin"
                            title="Admin"
                            icon={Shield}
                            description="Full platform control. Manage users, billing, and configurations."
                            features={['User Management', 'Billing & Plans', 'All Core Features']}
                            onSelect={setSelectedRole}
                            isSelected={selectedRole === 'admin'}
                        />
                        <RoleCard
                            role="engineer"
                            title="Engineer"
                            icon={Wrench}
                            description="Operational access. Manage models, assets, and simulations."
                            features={['Model Training', 'Asset Management', 'Simulations']}
                            onSelect={setSelectedRole}
                            isSelected={selectedRole === 'engineer'}
                        />
                        <RoleCard
                            role="viewer"
                            title="Viewer"
                            icon={Eye}
                            description="Read-only access. Monitor assets and view dashboards."
                            features={['View Dashboards', 'Monitor Assets', 'Read-only Mode']}
                            onSelect={setSelectedRole}
                            isSelected={selectedRole === 'viewer'}
                        />
                    </div>

                    <div className="relative z-10 flex justify-center">
                        <button
                            onClick={handleConfirm}
                            disabled={!selectedRole}
                            className={cn(
                                "px-8 py-3 rounded-full font-semibold transition-all duration-300",
                                selectedRole
                                    ? "bg-primary text-white hover:bg-primary/90 shadow-[0_0_20px_rgba(157,78,221,0.4)]"
                                    : "bg-white/10 text-white/30 cursor-not-allowed"
                            )}
                        >
                            Confirm Access
                        </button>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
