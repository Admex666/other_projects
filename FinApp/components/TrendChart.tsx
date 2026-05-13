'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function TrendChart({ data }: { data: any[] }) {
  // Transform data for recharts
  const months = ['Jan', 'Feb', 'Már', 'Ápr', 'Máj', 'Jún', 'Júl', 'Aug', 'Szep', 'Okt', 'Nov', 'Dec'];
  
  const formattedData = data.reduce((acc: any[], curr: any) => {
    const label = `${months[curr._id.month - 1]}`;
    let monthEntry = acc.find(m => m.name === label);
    
    if (!monthEntry) {
      monthEntry = { name: label, income: 0, expense: 0 };
      acc.push(monthEntry);
    }
    
    if (curr._id.type === 'income') monthEntry.income += curr.total;
    if (curr._id.type === 'expense') monthEntry.expense += curr.total;
    
    return acc;
  }, []);

  return (
    <div className="h-64 w-full mt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
          <XAxis 
            dataKey="name" 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
          />
          <YAxis 
            axisLine={false} 
            tickLine={false} 
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            tickFormatter={(value) => `${value / 1000}k`}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1A1A24', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px' }}
            itemStyle={{ fontSize: '12px' }}
            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
          />
          <Bar dataKey="income" fill="#4ADE80" radius={[4, 4, 0, 0]} barSize={12} />
          <Bar dataKey="expense" fill="#F87171" radius={[4, 4, 0, 0]} barSize={12} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
