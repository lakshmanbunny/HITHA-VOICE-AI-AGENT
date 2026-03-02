import { useState, useEffect, useRef } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Phone, PhoneOff, Mic, User, Bot, Loader2, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

// LiveKit Imports
import {
    LiveKitRoom,
    RoomAudioRenderer,
    ControlBar,
    useLocalParticipant,
    useTranscriptions,
} from "@livekit/components-react";

interface Message {
    speaker: "User" | "Assistant";
    text: string;
}

const DemoContent = ({ onEnd }: { onEnd: () => void }) => {
    const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
    const segments = useTranscriptions();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [messages, setMessages] = useState<Message[]>([]);

    // Sync transcription segments to message list
    useEffect(() => {
        const newMessages: Message[] = segments.map(s => ({
            speaker: s.participantInfo.identity === localParticipant?.identity ? "User" : "Assistant",
            text: s.text
        }));

        if (newMessages.length > 0) {
            setMessages(newMessages);
        }
    }, [segments]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="grid gap-6">
            <Card className="border-border/50 min-h-[500px] flex flex-col relative overflow-hidden">
                <CardHeader className="border-b border-border/50 flex flex-row items-center justify-between pb-3">
                    <div className="flex items-center gap-2">
                        <CardTitle className="text-base font-display">
                            {isMicrophoneEnabled ? "Listening..." : "Live Session"}
                        </CardTitle>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={onEnd}
                            className="gap-2"
                        >
                            <PhoneOff className="w-4 h-4" />
                            End Call
                        </Button>
                    </div>
                </CardHeader>

                <CardContent className="flex-1 flex flex-col p-0">
                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto p-6 space-y-4 max-h-[400px]"
                    >
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-center opacity-40 py-12">
                                <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mb-4">
                                    <Mic className="w-8 h-8" />
                                </div>
                                <p className="text-sm font-medium">Wait for Hitha to greet you, then speak...</p>
                            </div>
                        )}

                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "flex gap-3 max-w-[85%] animate-slide-up",
                                    msg.speaker === "User" ? "ml-auto flex-row-reverse" : "mr-auto"
                                )}
                            >
                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border",
                                    msg.speaker === "User" ? "bg-primary/10 border-primary/20 text-primary" : "bg-accent border-border text-foreground"
                                )}>
                                    {msg.speaker === "User" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                                </div>
                                <div className="space-y-1">
                                    <div className={cn(
                                        "p-3 rounded-2xl text-sm",
                                        msg.speaker === "User"
                                            ? "bg-primary text-primary-foreground rounded-tr-none"
                                            : "bg-secondary text-foreground rounded-tl-none"
                                    )}>
                                        {msg.text}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* LiveKit Controls */}
                    <div className="p-4 bg-secondary/30 border-t border-border/50 flex justify-center">
                        <ControlBar variation="minimal" controls={{ camera: false, screenShare: false, settings: false }} />
                    </div>
                </CardContent>
            </Card>

            <RoomAudioRenderer />
        </div>
    );
};

const Demo = () => {
    const [token, setToken] = useState<string | null>(null);
    const [isActive, setIsActive] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const { toast } = useToast();

    const startCall = async () => {
        setIsConnecting(true);
        try {
            const room = `demo-${Date.now()}`;
            const identity = `user-${Math.random().toString(36).slice(2, 8)}`;
            const response = await fetch(
                `http://${window.location.hostname}:8000/api/token?room=${encodeURIComponent(room)}&identity=${encodeURIComponent(identity)}`
            );
            if (!response.ok) throw new Error(`Token request failed: ${response.status}`);
            const data = await response.json();
            setToken(data.token);
            setIsActive(true);
            toast({ title: "Connecting...", description: "Joining LiveKit room." });
        } catch (err: any) {
            toast({ title: "Connection Error", description: err?.message || "Failed to get access token.", variant: "destructive" });
        } finally {
            setIsConnecting(false);
        }
    };

    const endCall = () => {
        setToken(null);
        setIsActive(false);
    };

    return (
        <DashboardLayout>
            <div className="animate-fade-in max-w-4xl mx-auto">
                <div className="mb-6 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-display font-bold text-foreground">Interactive Demo</h1>
                        <p className="text-muted-foreground text-sm mt-1">Test the voice assistant workflow via LiveKit Agent</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <Badge variant={isActive ? "default" : "secondary"} className={cn("px-3 py-1", isActive && "bg-success hover:bg-success")}>
                            {isActive ? "Connected" : "Disconnected"}
                        </Badge>
                    </div>
                </div>

                {!isActive ? (
                    <Card className="border-border/50 min-h-[300px] flex flex-col items-center justify-center text-center p-12">
                        <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
                            <Phone className="w-10 h-10 text-primary" />
                        </div>
                        <h2 className="text-xl font-display font-bold mb-2">Ready to start?</h2>
                        <p className="text-muted-foreground mb-8 max-w-md">
                            Start a demo call to connect with Hitha, your virtual hospital assistant.
                            The call uses your microphone and speakers.
                        </p>
                        <Button
                            size="lg"
                            onClick={startCall}
                            disabled={isConnecting}
                            className="gap-2 px-8 py-6 text-lg h-auto rounded-full shadow-lg hover:shadow-xl transition-all"
                        >
                            {isConnecting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Phone className="w-5 h-5" />}
                            {isConnecting ? "Connecting..." : "Start Demo Call"}
                        </Button>
                    </Card>
                ) : (
                    <LiveKitRoom
                        token={token!}
                        serverUrl={`wss://prototype-sei7ksgj.livekit.cloud`}
                        connect={true}
                        audio={true}
                        video={false}
                        onDisconnected={() => endCall()}
                    >
                        <DemoContent onEnd={endCall} />
                    </LiveKitRoom>
                )}

                <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card className="border-border/50">
                        <CardContent className="p-4">
                            <h3 className="text-sm font-bold mb-1">How it works</h3>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                This demo connects directly to a LiveKit Agent. We use Sarvam AI for
                                low-latency Indian language STT/TTS and Google Gemini for logic.
                            </p>
                        </CardContent>
                    </Card>
                    <Card className="border-border/50">
                        <CardContent className="p-4">
                            <h3 className="text-sm font-bold mb-1">Supported Languages</h3>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                Hitha can understand and speak in English, Hindi, and Telugu.
                                Try switching languages during the call!
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default Demo;
