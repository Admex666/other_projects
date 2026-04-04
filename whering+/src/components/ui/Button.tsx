import { ReactNode, ButtonHTMLAttributes } from 'react';
import styles from './Button.module.css';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'tertiary';
  fullWidth?: boolean;
  children: ReactNode;
}

export function Button({ variant = 'primary', fullWidth, className = '', children, ...props }: ButtonProps) {
  const classes = [
    styles.btn,
    styles[variant],
    fullWidth ? styles.fullWidth : '',
    className
  ].join(' ').trim();

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
