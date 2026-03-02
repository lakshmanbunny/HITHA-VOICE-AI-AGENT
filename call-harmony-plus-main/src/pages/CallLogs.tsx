import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCallLogs } from "@/services/api";
import { CallLog } from "@/types/dashboard";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PhoneIncoming, PhoneOutgoing, Eye, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const statusStyles: Record<string, string> = {
  completed: "bg-success/10 text-success border-success/20",
  transferred: "bg-warning/10 text-warning border-warning/20",
  "no-answer": "bg-muted text-muted-foreground border-border",
  failed: "bg-destructive/10 text-destructive border-destructive/20",
};

const CallLogs = () => {
  const [selectedCall, setSelectedCall] = useState<CallLog | null>(null);

  const { data: callLogs, isLoading } = useQuery({
    queryKey: ["calls"],
    queryFn: fetchCallLogs,
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading call logs...</span>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        <div className="mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">Call Logs</h1>
          <p className="text-muted-foreground text-sm mt-1">View all voice assistant call history and transcripts</p>
        </div>

        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-display">All Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Direction</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Caller</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Phone</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Languages</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Status</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Duration</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Time</th>
                    <th className="text-left py-3 px-3 text-muted-foreground font-medium">Transcript</th>
                  </tr>
                </thead>
                <tbody>
                  {(callLogs ?? []).map((call) => (
                    <tr key={call.id} className="border-b border-border/50 hover:bg-secondary/30 transition-colors">
                      <td className="py-3 px-3">
                        {call.direction === "inbound" ? (
                          <PhoneIncoming className="w-4 h-4 text-primary" />
                        ) : (
                          <PhoneOutgoing className="w-4 h-4 text-warning" />
                        )}
                      </td>
                      <td className="py-3 px-3 font-medium text-foreground">{call.callerName}</td>
                      <td className="py-3 px-3 text-muted-foreground">{call.phoneNumber}</td>
                      <td className="py-3 px-3">
                        <div className="flex gap-1 flex-wrap">
                          {call.languages.map((lang) => (
                            <Badge key={lang} variant="outline" className="text-xs py-0">
                              {lang}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-3">
                        <span className={cn("text-xs px-2 py-0.5 rounded-full border", statusStyles[call.status])}>
                          {call.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-muted-foreground">{call.duration}</td>
                      <td className="py-3 px-3 text-muted-foreground">
                        {new Date(call.timestamp).toLocaleDateString("en-IN", {
                          month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                        })}
                      </td>
                      <td className="py-3 px-3">
                        {call.transcript.length > 0 ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedCall(call)}
                            className="h-7 px-2"
                          >
                            <Eye className="w-3.5 h-3.5 mr-1" />
                            View
                          </Button>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(callLogs ?? []).length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-8">No call logs yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Transcript Dialog */}
        <Dialog open={!!selectedCall} onOpenChange={() => setSelectedCall(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-display flex items-center justify-between">
                <span>Call Transcript — {selectedCall?.callerName}</span>
              </DialogTitle>
              <div className="flex gap-2 text-xs text-muted-foreground pt-1">
                <span>{selectedCall?.phoneNumber}</span>
                <span>·</span>
                <span>{selectedCall?.duration}</span>
                <span>·</span>
                <span>{selectedCall?.languages.join(", ")}</span>
              </div>
            </DialogHeader>
            <div className="space-y-3 mt-4">
              {selectedCall?.transcript.map((entry, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-3 rounded-lg text-sm",
                    entry.speaker === "Assistant"
                      ? "bg-accent/60 ml-0 mr-8"
                      : "bg-secondary ml-8 mr-0"
                  )}
                >
                  <p className="text-xs font-medium text-muted-foreground mb-1">{entry.speaker}</p>
                  <p className="text-foreground">{entry.text}</p>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};

export default CallLogs;
