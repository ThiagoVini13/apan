import js from '@eslint/js'
import importPlugin from 'eslint-plugin-import'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'
import tseslint from 'typescript-eslint'

const FEATURES = [
  'audit',
  'auth',
  'classes',
  'dashboard',
  'reports',
  'roll-call',
  'school-years',
  'students',
  'subjects',
  'users',
]

const featureIsolation = FEATURES.map((feature) => ({
  target: `./src/features/${feature}`,
  from: './src/features',
  except: [`./${feature}`, ...FEATURES.filter((f) => f !== feature).map((f) => `./${f}/index.ts`)],
  message: 'Features import other features only through their index.ts.',
}))

export default tseslint.config(
  { ignores: ['dist', 'coverage', 'src/shared/api/schema.d.ts'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended, jsxA11y.flatConfigs.strict],
    files: ['**/*.{ts,tsx}'],
    languageOptions: { globals: globals.browser },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      import: importPlugin,
    },
    settings: {
      'import/resolver': { node: { extensions: ['.ts', '.tsx'] } },
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      'no-console': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', ignoreRestSiblings: true },
      ],
      'jsx-a11y/no-noninteractive-tabindex': ['error', { tags: [], roles: ['tabpanel', 'region'] }],
      'import/no-restricted-paths': [
        'error',
        {
          zones: [
            ...featureIsolation,
            {
              target: './src/shared',
              from: ['./src/features', './src/app'],
              message: 'shared/ never depends on features/ or app/.',
            },
            {
              target: './src/stores',
              from: ['./src/features', './src/app'],
              message: 'stores/ never depends on features/ or app/.',
            },
          ],
        },
      ],
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/features/*/*'],
              message: 'Import other features through @/features/<name> (index.ts).',
            },
          ],
        },
      ],
    },
  },
  {
    files: ['src/test/**', '**/*.test.{ts,tsx}'],
    rules: { 'no-restricted-imports': 'off' },
  },
)
