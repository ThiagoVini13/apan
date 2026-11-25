import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'
import { fieldErrorMessage, messageForCode } from './errors'
import { ApiError } from './http'

/**
 * Maps API field errors onto the form. Returns the message for a summary when the error
 * is not tied to a known field (or is not an ApiError at all).
 */
export function applyApiErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
): string | null {
  if (!(error instanceof ApiError)) return messageForCode('internal_error')
  const known = new Set<string>(fields)
  let mapped = false
  for (const fieldError of error.fieldErrors) {
    if (known.has(fieldError.field)) {
      setError(
        fieldError.field as Path<T>,
        { type: 'server', message: fieldErrorMessage(fieldError.code) },
        { shouldFocus: !mapped },
      )
      mapped = true
    }
  }
  return mapped ? null : messageForCode(error.code)
}
