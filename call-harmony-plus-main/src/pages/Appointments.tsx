import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAppointments, updateAppointment, cancelAppointment as cancelApt } from "@/services/api";
import { Appointment } from "@/types/dashboard";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Clock, Stethoscope, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

const statusBadge: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
  confirmed: { variant: "default", label: "Confirmed" },
  rescheduled: { variant: "secondary", label: "Rescheduled" },
  cancelled: { variant: "destructive", label: "Cancelled" },
  completed: { variant: "outline", label: "Completed" },
};

const Appointments = () => {
  const [selectedApt, setSelectedApt] = useState<Appointment | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: appointments, isLoading } = useQuery({
    queryKey: ["appointments"],
    queryFn: fetchAppointments,
  });

  const rescheduleMutation = useMutation({
    mutationFn: (id: string) => updateAppointment(id, { status: "rescheduled" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      toast({ title: "Appointment Rescheduled", description: `${selectedApt?.patientName}'s appointment has been rescheduled.` });
      setSelectedApt(null);
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelApt(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      toast({ title: "Appointment Cancelled", description: `${selectedApt?.patientName}'s appointment has been cancelled.` });
      setSelectedApt(null);
    },
    onError: (err: Error) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    },
  });

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading appointments...</span>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        <div className="mb-6">
          <h1 className="text-2xl font-display font-bold text-foreground">Appointments</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage all scheduled patient appointments</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(appointments ?? []).map((apt) => {
            const badge = statusBadge[apt.status] || statusBadge.confirmed;
            return (
              <Card
                key={apt.id}
                className={cn(
                  "border-border/50 cursor-pointer hover:shadow-md transition-shadow",
                  apt.status === "cancelled" && "opacity-60"
                )}
                onClick={() => setSelectedApt(apt)}
              >
                <CardContent className="p-5">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-semibold text-foreground font-display">{apt.patientName}</p>
                      <p className="text-xs text-muted-foreground">{apt.phoneNumber}</p>
                    </div>
                    <Badge variant={badge.variant} className="text-xs">{badge.label}</Badge>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Stethoscope className="w-3.5 h-3.5" />
                      <span>{apt.doctorName} · {apt.department}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="w-3.5 h-3.5" />
                      <span>
                        {new Date(apt.dateTime).toLocaleDateString("en-IN", {
                          weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                        })}
                      </span>
                    </div>
                    {apt.symptoms.length > 0 && (
                      <div className="flex items-start gap-2 text-muted-foreground">
                        <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                        <span>{apt.symptoms.join(", ")}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {(appointments ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8 col-span-full">No appointments yet</p>
          )}
        </div>

        {/* Appointment Detail Dialog */}
        <Dialog open={!!selectedApt} onOpenChange={() => setSelectedApt(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="font-display">Appointment Details</DialogTitle>
            </DialogHeader>
            {selectedApt && (
              <div className="space-y-4 mt-2">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Patient</p>
                    <p className="font-medium text-foreground">{selectedApt.patientName}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Phone</p>
                    <p className="font-medium text-foreground">{selectedApt.phoneNumber}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Doctor</p>
                    <p className="font-medium text-foreground">{selectedApt.doctorName}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Department</p>
                    <p className="font-medium text-foreground">{selectedApt.department}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Date & Time</p>
                    <p className="font-medium text-foreground">
                      {new Date(selectedApt.dateTime).toLocaleDateString("en-IN", {
                        weekday: "long", month: "long", day: "numeric", year: "numeric",
                        hour: "2-digit", minute: "2-digit",
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Status</p>
                    <Badge variant={statusBadge[selectedApt.status]?.variant || "default"}>
                      {statusBadge[selectedApt.status]?.label || selectedApt.status}
                    </Badge>
                  </div>
                </div>

                {selectedApt.symptoms.length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Symptoms</p>
                    <div className="flex gap-1.5 flex-wrap">
                      {selectedApt.symptoms.map((s) => (
                        <Badge key={s} variant="outline" className="text-xs">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedApt.callId && (
                  <div>
                    <p className="text-xs text-muted-foreground">Associated Call</p>
                    <p className="text-sm font-medium text-primary">{selectedApt.callId}</p>
                  </div>
                )}
              </div>
            )}
            <DialogFooter className="gap-2 mt-4">
              {selectedApt?.status !== "cancelled" && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => selectedApt && rescheduleMutation.mutate(selectedApt.id)}
                    disabled={rescheduleMutation.isPending}
                  >
                    {rescheduleMutation.isPending ? "Rescheduling..." : "Reschedule"}
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => selectedApt && cancelMutation.mutate(selectedApt.id)}
                    disabled={cancelMutation.isPending}
                  >
                    {cancelMutation.isPending ? "Cancelling..." : "Cancel Appointment"}
                  </Button>
                </>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};

export default Appointments;
