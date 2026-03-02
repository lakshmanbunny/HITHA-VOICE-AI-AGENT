import { useQuery } from "@tanstack/react-query";
import { fetchStats, fetchCallLogs, fetchAppointments } from "@/services/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PhoneCall, CalendarCheck, PhoneMissed, ArrowRightLeft, TrendingUp, Clock, Loader2 } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";

const DashboardOverview = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
  });
  const { data: callLogs, isLoading: callsLoading } = useQuery({
    queryKey: ["calls"],
    queryFn: fetchCallLogs,
  });
  const { data: appointments, isLoading: aptsLoading } = useQuery({
    queryKey: ["appointments"],
    queryFn: fetchAppointments,
  });

  const isLoading = statsLoading || callsLoading || aptsLoading;

  const statCards = stats
    ? [
      { label: "Total Calls", value: stats.totalCalls, icon: PhoneCall, color: "text-primary" },
      { label: "Appointments", value: stats.totalAppointments, icon: CalendarCheck, color: "text-success" },
      { label: "Calls Today", value: stats.callsToday, icon: TrendingUp, color: "text-info" },
      { label: "Missed Calls", value: stats.missedCalls, icon: PhoneMissed, color: "text-destructive" },
      { label: "Transferred", value: stats.transferredCalls, icon: ArrowRightLeft, color: "text-warning" },
      { label: "Today's Appts", value: stats.appointmentsToday, icon: Clock, color: "text-accent-foreground" },
    ]
    : [];

  const recentCalls = callLogs?.slice(0, 3) ?? [];
  const upcomingAppointments = appointments?.filter(a => a.status !== "cancelled").slice(0, 3) ?? [];

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading dashboard...</span>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="animate-fade-in">
        <div className="mb-8">
          <h1 className="text-2xl font-display font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground text-sm mt-1">Overview of your hospital voice assistant</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {statCards.map((stat) => (
            <Card key={stat.label} className="border-border/50">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-xs text-muted-foreground">{stat.label}</span>
                </div>
                <p className="text-2xl font-bold font-display text-foreground">{stat.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Recent Calls */}
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">Recent Calls</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentCalls.map((call) => (
                <div key={call.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="font-medium text-sm text-foreground">{call.callerName}</p>
                    <p className="text-xs text-muted-foreground">{call.phoneNumber}</p>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1">
                    <Badge variant={call.direction === "inbound" ? "default" : "secondary"} className="text-xs">
                      {call.direction === "inbound" ? "Inbound" : "Outbound"}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{call.duration}</span>
                  </div>
                </div>
              ))}
              {recentCalls.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">No calls yet</p>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Appointments */}
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-display">Upcoming Appointments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingAppointments.map((apt) => (
                <div key={apt.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="font-medium text-sm text-foreground">{apt.patientName}</p>
                    <p className="text-xs text-muted-foreground">{apt.doctorName} · {apt.department}</p>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1">
                    <Badge
                      variant={apt.status === "confirmed" ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {apt.status}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(apt.dateTime).toLocaleDateString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              ))}
              {upcomingAppointments.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">No upcoming appointments</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardOverview;
