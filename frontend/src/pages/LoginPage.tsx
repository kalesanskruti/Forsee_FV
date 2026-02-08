import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { AuthComponent } from "@/components/ui/AuthComponent";
import { toast } from "sonner";
import { Gem } from "lucide-react";

export default function LoginPage() {
    const { login, loginWithGoogle } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from?.pathname || "/";

    const handleSignIn = async (data: any) => {
        try {
            await login(data.email, data.password);
            navigate(from, { replace: true });
        } catch (error) {
            throw error; // Rethrow to let AuthComponent handle modal error state
        }
    };

    const handleGoogleSignIn = async () => {
        try {
            await loginWithGoogle();
            navigate(from, { replace: true });
        } catch (error) {
            toast.error("Google sign in failed.");
            throw error;
        }
    };

    const handleSwitchToSignup = () => {
        navigate("/signup");
    };

    const handleLegalClick = () => {
        navigate("/legal");
    };

    return (
        <AuthComponent
            mode="signin"
            onAuth={handleSignIn}
            onGoogleLogin={handleGoogleSignIn}
            onSwitchMode={handleSwitchToSignup}
            onLegalClick={handleLegalClick}
            brandName="Forsee AI"
        />
    );
}
