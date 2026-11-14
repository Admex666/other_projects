import FacilitatorPinGate from '@/components/facilitator/FacilitatorPinGate'

export default function FacilitatorLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <FacilitatorPinGate>{children}</FacilitatorPinGate>
}
