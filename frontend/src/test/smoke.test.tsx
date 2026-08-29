import { render, screen } from '@testing-library/react'

// تست دود: زیرساخت تست سالم است؟
test('زیرساخت تست کار می‌کند', () => {
  expect(1 + 1).toBe(2)
})

test('jsdom محیط DOM را شبیه‌سازی می‌کند', () => {
  const div = document.createElement('div')
  div.textContent = 'سلام اکونوژین'
  document.body.appendChild(div)
  expect(screen.getByText('سلام اکونوژین')).toBeInTheDocument()
})