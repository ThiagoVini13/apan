import { axe } from 'vitest-axe'
import { expect } from 'vitest'

type Theme = 'light' | 'dark'

async function violationsIn(theme: Theme, container: Element) {
  document.documentElement.classList.toggle('dark', theme === 'dark')
  const results = await axe(container, {
    rules: {
      // jsdom does not compute styles from CSS variables; contrast is verified with the
      // token table in index.css instead.
      'color-contrast': { enabled: false },
    },
  })
  return results.violations.map((violation) => ({
    theme,
    id: violation.id,
    help: violation.help,
    nodes: violation.nodes.map((node) => node.target.join(' ')),
  }))
}

export async function expectNoA11yViolations(container: Element = document.body) {
  const violations = [
    ...(await violationsIn('light', container)),
    ...(await violationsIn('dark', container)),
  ]
  document.documentElement.classList.remove('dark')
  expect(violations).toEqual([])
}
