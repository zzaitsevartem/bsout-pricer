export {
  registerRequestSchema,
  loginRequestSchema,
  tokenResponseSchema,
  refreshRequestSchema,
  passwordResetRequestSchema,
  passwordResetConfirmSchema,
  messageResponseSchema,
  vkAuthorizeResponseSchema,
  vkCallbackRequestSchema,
  vkAuthResponseSchema,
} from './schema';
export type {
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  RefreshRequest,
  PasswordResetRequest,
  PasswordResetConfirm,
  MessageResponse,
  VkAuthorizeResponse,
  VkCallbackRequest,
  VkAuthResponse,
} from './schema';
export { authApi } from './service';
export {
  useRegister,
  useLogin,
  useLogout,
  useUsernameAvailable,
  useRequestPasswordReset,
  useConfirmPasswordReset,
  useVkAuthorize,
  useVkCallback,
} from './hooks';
