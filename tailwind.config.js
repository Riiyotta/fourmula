/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        mainbg: 'var(--mainbg)',
        'mainbg-gradient': 'var(--mainbg-gradient)',
        secondbg: 'var(--secondbg)',
        menu: 'var(--menu)',
        'menu-colors': 'var(--menu-colors)',
        lines: 'var(--lines)',
        dots: 'var(--dots-pattern)',
        'fonts-100': 'var(--fonts-100)',
        'fonts-64': 'var(--fonts-64)',
        'fonts-50': 'var(--fonts-50)',
        'fonts-30': 'var(--fonts-30)',
        'fonts-20': 'var(--fonts-20)',
      },
      fontFamily: {
        sans: ['Sf Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Arial', 'sans-serif'],
      },
      fontSize: {
        h1: 'var(--_fonts---h1)',
        h2: 'var(--_fonts---h2)',
        'h2-5': 'var(--_fonts---h2-5)',
        h3: 'var(--_fonts---h3)',
        h4: 'var(--_fonts---h4)',
        'title-1': 'var(--_fonts---title-1)',
        'title-2': 'var(--_fonts---title-2)',
        'title-3': 'var(--_fonts---title-3)',
        'body-1': 'var(--_fonts---body-1)',
        'body-2': 'var(--_fonts---body-2)',
        'body-3': 'var(--_fonts---body-3)',
        tag: 'var(--_fonts---tag)',
        'tag-small': 'var(--_fonts---tag-small)',
        btn: 'var(--_fonts---btn)',
        'small-1': 'var(--_fonts---small-text-1)',
        'small-2': 'var(--_fonts---small-text-2)',
      },
      screens: {
        'wf-md': { max: '991px' },
        'wf-sm': { max: '767px' },
        'wf-xs': { max: '479px' },
      },
    },
  },
  plugins: [],
}
