import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { useDetectEventMutation } from "@/lib/api/queries";
import { toast } from "sonner";
import { Sparkles, Zap } from "lucide-react";
import type { Scenario } from "@/types/api";

interface SimulateEventDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  merchantId?: string;
  onSuccess?: (caseId: string) => void;
}

export function SimulateEventDialog({
  open,
  onOpenChange,
  merchantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
  onSuccess,
}: SimulateEventDialogProps) {
  const [scenario, setScenario] = useState<Scenario>("PAYMENT_FAILURE");
  const [customerName, setCustomerName] = useState("Rajesh Kumar");
  const [customerSegment, setCustomerSegment] = useState("LOYAL");
  const [amountRupees, setAmountRupees] = useState("2499");
  const [reasonCode, setReasonCode] = useState("INSUFFICIENT_FUNDS");

  const detectMutation = useDetectEventMutation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const amountPaise = Math.round(parseFloat(amountRupees || "0") * 100);

    if (isNaN(amountPaise) || amountPaise <= 0) {
      toast.error("Please enter a valid positive amount in Rupees.");
      return;
    }

    detectMutation.mutate(
      {
        merchant_id: merchantId,
        customer_id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : undefined,
        customer_name: customerName,
        customer_segment: customerSegment as any,
        event_type: scenario,
        amount_paise: amountPaise,
        reason_code: reasonCode,
      },
      {
        onSuccess: (res: any) => {
          const caseId = res?.case_id || res?.data?.case_id;
          if (!caseId) {
            toast.error("Event recorded, but case ID was not returned.");
            return;
          }
          toast.success(`Revenue event detected! Case ID: ${caseId}`);
          onOpenChange(false);
          if (onSuccess) {
            onSuccess(caseId);
          }
        },
        onError: (err) => {
          toast.error(err.message || "Failed to simulate revenue event.");
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base font-bold">
            <Sparkles className="w-4 h-4 text-indigo-500" /> Simulate Real-Time Revenue Event
          </DialogTitle>
          <DialogDescription className="text-xs">
            Trigger a live webhook simulation (Payment failure, Checkout dropoff, Subscription decline, or Overdue receivable).
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 py-2 text-xs">
          <div className="space-y-1">
            <Label className="text-xs font-semibold">Revenue Failure Scenario</Label>
            <Select value={scenario} onValueChange={(val) => setScenario(val as Scenario)}>
              <SelectTrigger className="text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PAYMENT_FAILURE" className="text-xs">Payment Failure (Card/UPI Decline)</SelectItem>
                <SelectItem value="CHECKOUT_ABANDONMENT" className="text-xs">Checkout Abandonment (Cart Timeout)</SelectItem>
                <SelectItem value="SUBSCRIPTION_FAILURE" className="text-xs">Subscription Failure (Card Expired)</SelectItem>
                <SelectItem value="OVERDUE_RECEIVABLE" className="text-xs">Overdue Receivable (B2B Invoice)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-semibold">Customer Name</Label>
              <Input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="e.g. Ananya Sharma"
                className="text-xs"
                required
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs font-semibold">Customer Segment</Label>
              <Select value={customerSegment} onValueChange={setCustomerSegment}>
                <SelectTrigger className="text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LOYAL" className="text-xs">Loyal (High LTV)</SelectItem>
                  <SelectItem value="HIGH_VALUE" className="text-xs">High Value</SelectItem>
                  <SelectItem value="REGULAR" className="text-xs">Regular</SelectItem>
                  <SelectItem value="NEW" className="text-xs">New Customer</SelectItem>
                  <SelectItem value="AT_RISK" className="text-xs">At Risk</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs font-semibold">Amount At Risk (₹ INR)</Label>
              <Input
                type="number"
                value={amountRupees}
                onChange={(e) => setAmountRupees(e.target.value)}
                placeholder="e.g. 2499"
                className="text-xs font-mono"
                required
              />
            </div>

            <div className="space-y-1">
              <Label className="text-xs font-semibold">Gateway Reason Code</Label>
              <Input
                value={reasonCode}
                onChange={(e) => setReasonCode(e.target.value)}
                placeholder="e.g. BANK_TIMEOUT"
                className="text-xs font-mono"
              />
            </div>
          </div>

          <DialogFooter className="pt-3 border-t border-border/40">
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={detectMutation.isPending}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs"
            >
              {detectMutation.isPending ? "Detecting..." : <><Zap className="w-3.5 h-3.5 mr-1" /> Trigger Live Event</>}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
