import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { AuthComponent } from "@/components/ui/AuthComponent";
import { toast } from "sonner";

export default function SignupPage() {
    const { signup, loginWithGoogle } = useAuth();
    const navigate = useNavigate();

    const handleSignup = async (data: any) => {
        try {
            await signup(data.name, data.email, data.password);
            // Redirection happens after success animation in component? 
            // No, the component just shows success. I should probably handle navigation here or in component.
            // Let's navigate after a short delay for the user to see success.
            setTimeout(() => navigate("/"), 2500);
        } catch (error) {
            throw error;
        }
    };

    const handleGoogleSignUp = async () => {
        try {
            await loginWithGoogle();
            navigate("/");
        } catch (error) {
            toast.error("Google sign up failed.");
            throw error;
        }
    };

    const handleSwitchToSignin = () => {
        navigate("/login");
    };

    const handleLegalClick = () => {
        navigate("/legal");
    };

    return (
        <AuthComponent
            mode="signup"
            onAuth={handleSignup}
            onGoogleLogin={handleGoogleSignUp}
            onSwitchMode={handleSwitchToSignin}
            onLegalClick={handleLegalClick}
            brandName="Forsee AI"
        />
    );
}
