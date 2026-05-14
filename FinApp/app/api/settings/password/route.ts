import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import dbConnect from '@/lib/mongodb';
import { User } from '@/models/User';
import bcrypt from 'bcryptjs';

export async function POST(req: Request) {
  try {
    const session = await getServerSession(authOptions);
    if (!session?.user) {
      return NextResponse.json({ error: 'Nincs bejelentkezve' }, { status: 401 });
    }

    const { password, confirmPassword } = await req.json();

    if (!password || password.length < 6) {
      return NextResponse.json({ error: 'A jelszónak legalább 6 karakternek kell lennie' }, { status: 400 });
    }

    if (password !== confirmPassword) {
      return NextResponse.json({ error: 'A két jelszó nem egyezik' }, { status: 400 });
    }

    await dbConnect();
    const hashedPassword = await bcrypt.hash(password, 10);

    const userId = (session.user as any).id;
    await User.findByIdAndUpdate(userId, { password: hashedPassword });

    return NextResponse.json({ message: 'Jelszó sikeresen megváltoztatva' });
  } catch (error) {
    console.error('Password update error:', error);
    return NextResponse.json({ error: 'Szerver hiba történt' }, { status: 500 });
  }
}
