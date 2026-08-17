import React from 'react';
import { sound } from '../../utils/sound';
import { triggerHaptic } from '../../utils/haptics';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'glow' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  fullWidth = false,
  className = '',
  onClick,
  disabled,
  ...props
}) => {
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    sound.playClick();
    triggerHaptic('light');
    if (onClick) onClick(e);
  };

  const baseStyles =
    'relative inline-flex items-center justify-center font-bold tracking-wide rounded-xl transition-transform active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none disabled:active:scale-100 select-none';

  const sizeStyles = {
    sm: 'px-3.5 py-2 text-sm gap-1.5',
    md: 'px-4 py-3 text-base gap-2',
    lg: 'px-5 py-3.5 text-base sm:text-lg gap-2.5',
  };

  const variantStyles = {
    primary:
      'bg-amber-500 hover:bg-amber-400 text-slate-950 border border-amber-400 font-extrabold',
    glow:
      'bg-amber-500 hover:bg-amber-400 text-slate-950 border border-amber-300 font-black',
    secondary:
      'bg-[#161F32] hover:bg-[#1E293B] text-slate-200 border border-[#28354D]',
    danger:
      'bg-rose-600 hover:bg-rose-500 text-white border border-rose-500',
    ghost:
      'bg-transparent hover:bg-slate-800 text-slate-300 border border-transparent',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      onClick={handleClick}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};
