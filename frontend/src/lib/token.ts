/**
 * In-memory JWT token store.
 *
 * Agent.md §12: "JWT in memory — never localStorage or sessionStorage."
 * The token is a module-level variable. It lives only as long as the tab is open.
 * On refresh the user must re-authenticate — this is by design for security.
 *
 * The Axios interceptor reads getToken() on every request, so any component that
 * calls setToken() will automatically authenticate subsequent requests.
 */

let accessToken: string | null = null

/** Store the JWT received from /api/v1/auth/login */
export const setToken = (token: string): void => {
  accessToken = token
}

/** Retrieve the current JWT (null if not authenticated) */
export const getToken = (): string | null => accessToken

/** Clear the JWT (called on logout) */
export const clearToken = (): void => {
  accessToken = null
}

/** True if a token is currently held in memory */
export const isAuthenticated = (): boolean => accessToken !== null
