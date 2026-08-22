"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useTheme } from "@/lib/theme-context";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Motor {
  type: string;
  name: string;
  icon: string;
  description: string;
  inputs: string[];
}

interface MotorRunRequest {
  motor_type: string;
  scenario_name: string;
  start_date: string;
  end_date: string;
  time_step: string;
  region_bounds: number[];
  parameters: Record<string, any>;
}

interface MotorStatus {
  run_id: string;
  status: "running" | "completed" | "failed";
  summary?: Record<string, { min: number; max: number; mean: number }>;
  error_message?: string;
  execution_time?: number;
  outputs_keys?: string[];
}

function useMotorsList() {
  return useQuery({
    queryKey: ["motors", "list"],
    queryFn: async () => {
      const res = await api.get<{ motors: Motor[] }>("/api/motors/list");
      if (!res.success) throw new Error(res.error);
      return res.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

function useMotorStatus(runId: string | null) {
  return useQuery({
    queryKey: ["motors", "status", runId],
    queryFn: async () => {
      const res = await api.get<MotorStatus>(`/api/motors/status/${runId}`);
      if (!res.success) throw new Error(res.error);
      return res.data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" ? 1000 : false;
    },
  });
}

function useRunMotor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (request: MotorRunRequest) => {
      const res = await api.post<{ run_id: string; status: string }>(
        "/api/motors/run",
        request
      );
      if (!res.success) throw new Error(res.error);
      return res.data;
    },
    onSuccess: (data: any) => {
      toast.success(`موتور شروع شد: ${data.run_id}`);
      queryClient.invalidateQueries({ queryKey: ["motors"] });
    },
    onError: (error: Error) => {
      toast.error(`خطا در اجرای موتور: ${error.message}`);
    },
  });
}

export function MotorsDashboard() {
  const { colors } = useTheme();
  const [selectedMotor, setSelectedMotor] = useState<string>("");
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [params, setParams] = useState({
    scenario_name: "baseline",
    crop: "wheat",
    years: 20,
  });

  const { data: motorsData, isLoading: loadingMotors } = useMotorsList();
  const { data: statusData } = useMotorStatus(currentRunId);
  const runMotorMutation = useRunMotor();

  const motors = motorsData?.motors || [];
  const selected = motors.find((m) => m.type === selectedMotor);

  function handleRunMotor() {
    if (!selectedMotor) {
      toast.error("لطفاً یک موتور انتخاب کنید");
      return;
    }

    const parameters: Record<string, any> = {};
    if (selectedMotor === "aquacrop") parameters.crop = params.crop;
    if (selectedMotor === "rothc") parameters.years = params.years;
    if (selectedMotor === "hecras") parameters.return_period = 100;

    runMotorMutation.mutate(
      {
        motor_type: selectedMotor,
        scenario_name: params.scenario_name,
        start_date: "2026-01-01",
        end_date: "2026-12-31",
        time_step: "daily",
        region_bounds: [51.0, 35.0, 51.05, 35.05],
        parameters,
      },
      {
        onSuccess: (data: any) => {
          setCurrentRunId(data.run_id);
        },
      }
    );
  }

  return (
    <div className="space-y-6">
      <Card style={{ background: colors.cardBg, borderColor: colors.cardBorder }}>
        <CardHeader>
          <CardTitle className="text-xl">انتخاب موتور علمی</CardTitle>
          <CardDescription>
            یکی از پنج موتور علمی را برای شبیه‌سازی انتخاب کنید
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingMotors ? (
            <div className="text-center py-8" style={{ color: colors.textMuted }}>
              در حال بارگذاری موتورها...
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {motors.map((motor) => (
                <motion.button
                  key={motor.type}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => setSelectedMotor(motor.type)}
                  className="p-4 rounded-lg border-2 transition-all text-right"
                  style={{
                    borderColor: selectedMotor === motor.type ? colors.primary : colors.border,
                    background: selectedMotor === motor.type ? `${colors.primary}15` : "transparent",
                  }}
                >
                  <div className="text-3xl mb-2">{motor.icon}</div>
                  <div className="font-semibold text-sm mb-1">{motor.name}</div>
                  <div className="text-xs" style={{ color: colors.textMuted }}>
                    {motor.description}
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {selected && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card style={{ background: colors.cardBg, borderColor: colors.cardBorder }}>
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <span>{selected.icon}</span>
                پارامترهای {selected.name}
              </CardTitle>
              <CardDescription>تنظیمات سناریو را مشخص کنید</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>نام سناریو</Label>
                  <Input
                    value={params.scenario_name}
                    onChange={(e) => setParams({ ...params, scenario_name: e.target.value })}
                    placeholder="baseline"
                  />
                </div>

                {selectedMotor === "aquacrop" && (
                  <div className="space-y-2">
                    <Label>نوع محصول</Label>
                    <Select
                      value={params.crop}
                      onValueChange={(v) => setParams({ ...params, crop: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="wheat">گندم</SelectItem>
                        <SelectItem value="maize">ذرت</SelectItem>
                        <SelectItem value="barley">جو</SelectItem>
                        <SelectItem value="cotton">پنبه</SelectItem>
                        <SelectItem value="tomato">گوجه فرنگی</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {selectedMotor === "rothc" && (
                  <div className="space-y-2">
                    <Label>سال‌های شبیه‌سازی</Label>
                    <Input
                      type="number"
                      min="1"
                      max="100"
                      value={params.years}
                      onChange={(e) =>
                        setParams({ ...params, years: parseInt(e.target.value) })
                      }
                    />
                  </div>
                )}
              </div>

              <Button
                onClick={handleRunMotor}
                disabled={runMotorMutation.isPending}
                size="lg"
                className="w-full md:w-auto"
                style={{ background: colors.primary }}
              >
                {runMotorMutation.isPending ? "⏳ در حال شروع..." : "🚀 اجرای موتور"}
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      <AnimatePresence>
        {statusData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card style={{ background: colors.cardBg, borderColor: colors.cardBorder }}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">نتایج</CardTitle>
                  <StatusBadge status={statusData.status} />
                </div>
                {statusData.execution_time && (
                  <CardDescription>
                    زمان اجرا: {statusData.execution_time.toFixed(2)} ثانیه
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {statusData.error_message && (
                  <div
                    className="p-4 rounded-lg border"
                    style={{ background: `${colors.danger}15`, borderColor: colors.danger }}
                  >
                    <div className="font-semibold mb-1" style={{ color: colors.danger }}>
                      خطا:
                    </div>
                    <div className="text-sm">{statusData.error_message}</div>
                  </div>
                )}

                {statusData.summary && Object.keys(statusData.summary).length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-3">خلاصه آماری:</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(statusData.summary).map(([key, stats]) => (
                        <div
                          key={key}
                          className="p-3 rounded-lg border"
                          style={{ background: `${colors.accent}10`, borderColor: colors.border }}
                        >
                          <div className="font-medium mb-2 text-sm">{key}</div>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <StatItem label="حداقل" value={stats.min} />
                            <StatItem label="حداکثر" value={stats.max} />
                            <StatItem label="میانگین" value={stats.mean} highlight />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {statusData.outputs_keys && statusData.outputs_keys.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">لایه‌های خروجی:</h3>
                    <div className="flex flex-wrap gap-2">
                      {statusData.outputs_keys.map((key) => (
                        <Badge key={key} variant="secondary">
                          {key}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    running: { label: "در حال اجرا", color: "#f59e0b", bg: "#fef3c7" },
    completed: { label: "تکمیل شد", color: "#16a34a", bg: "#dcfce7" },
    failed: { label: "ناموفق", color: "#dc2626", bg: "#fee2e2" },
  }[status] || { label: status, color: "#6b7280", bg: "#f3f4f6" };

  return (
    <Badge
      style={{
        background: config.bg,
        color: config.color,
        border: `1px solid ${config.color}40`,
      }}
    >
      {config.label}
    </Badge>
  );
}

function StatItem({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  const { colors } = useTheme();
  return (
    <div className="text-center">
      <div style={{ color: colors.textMuted }}>{label}</div>
      <div
        className="font-mono font-semibold"
        style={{ color: highlight ? colors.primary : colors.text }}
      >
        {value?.toFixed(2) ?? "—"}
      </div>
    </div>
  );
}
