/** TanStack Query hooks for Bazargah plan-v2.0 services (disputes, logistics, quality). */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createDispute,
  createInspection,
  createShipment,
  escalateDispute,
  getShipment,
  listDisputes,
  listInspections,
  recordInspectionResult,
  updateShipmentStatus,
} from '../lib/bazargahV2Api';

// --- Disputes ---

export function useDisputes(status?: string) {
  return useQuery({
    queryKey: ['disputes', status ?? 'all'],
    queryFn: () => listDisputes(status),
    staleTime: 30_000,
    retry: false,
  });
}

export function useCreateDispute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createDispute,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['disputes'] }),
  });
}

export function useEscalateDispute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ disputeId, actor }: { disputeId: string; actor: string }) =>
      escalateDispute(disputeId, actor),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['disputes'] }),
  });
}

// --- Logistics ---

export function useShipment(shipmentId: string | undefined) {
  return useQuery({
    queryKey: ['shipment', shipmentId],
    queryFn: () => getShipment(shipmentId as string),
    enabled: !!shipmentId,
    retry: false,
  });
}

export function useCreateShipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createShipment,
    onSuccess: (data) => qc.invalidateQueries({ queryKey: ['shipment', data.id] }),
  });
}

export function useUpdateShipmentStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ shipmentId, ...payload }: { shipmentId: string; status: string; actor?: string; note?: string }) =>
      updateShipmentStatus(shipmentId, payload),
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: ['shipment', vars.shipmentId] }),
  });
}

// --- Quality ---

export function useInspections(productId?: string) {
  return useQuery({
    queryKey: ['inspections', productId ?? 'all'],
    queryFn: () => listInspections(productId),
    staleTime: 30_000,
    retry: false,
  });
}

export function useCreateInspection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createInspection,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inspections'] }),
  });
}

export function useRecordInspectionResult() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ inspectionId, ...payload }: { inspectionId: string; score: number; notes?: string }) =>
      recordInspectionResult(inspectionId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inspections'] }),
  });
}
