import DebtsClient from '@/components/DebtsClient';

export const metadata = {
  title: 'Tartozások | FinSpace',
  description: 'Splitwise-szerű elszámolás és közös költések',
};

export default function DebtsPage() {
  return <DebtsClient />;
}
