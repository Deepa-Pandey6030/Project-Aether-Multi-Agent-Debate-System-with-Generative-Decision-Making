export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      animation: {
        'fade-in': 'fade-in 0.4s ease-out forwards',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
  safelist: [
    'bg-blue-500/20', 'border-blue-500/50', 'text-blue-300', 'bg-blue-500/5', 'border-blue-500/20',
    'bg-red-500/20', 'border-red-500/50', 'text-red-300', 'bg-red-500/5', 'border-red-500/20',
    'bg-amber-500/20', 'border-amber-500/50', 'text-amber-300',
    'text-blue-400', 'text-red-400', 'text-amber-400', 'text-emerald-400',
  ],
}