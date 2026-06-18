export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  const payload = error?.response?.data

  if (typeof payload === 'string') {
    return payload
  }

  if (payload?.detail) {
    return payload.detail
  }

  if (payload && typeof payload === 'object') {
    const firstValue = Object.values(payload)[0]
    if (Array.isArray(firstValue)) {
      return firstValue[0]
    }
    if (typeof firstValue === 'string') {
      return firstValue
    }
  }

  return fallback
}
