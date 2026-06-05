import { isAxiosError } from "axios";
import { toast } from "vue-sonner";

import pinia from "@/plugins/pinia/setup";
import { useAuthStore } from "@/stores/auth";
import { useAxios } from "./use-axios";

const LOGIN_SUCCESS_CODE = 200;
const CAPTCHA_ERROR_CODE = 40001;
const DEFAULT_LOGIN_ERROR = "Login failed";

interface LoginPayload {
  username: string;
  password: string;
  uuid?: string;
  captcha?: string;
}

interface LoginResponseData {
  access_token: string;
  access_token_expire_time?: number;
  session_uuid: string;
  user: any;
}

interface LoginResponse {
  code: number;
  msg?: string;
  data?: LoginResponseData;
}

interface ErrorResponse {
  code?: number;
  msg?: string;
  message?: string;
}

type AuthError = Error & { code?: number };

function createAuthError(message: string, code?: number): AuthError {
  const error = new Error(message) as AuthError;
  error.code = code;
  return error;
}

function buildLoginPayload(
  username: string,
  password: string,
  uuid?: string,
  captcha?: string,
): LoginPayload {
  const payload: LoginPayload = {
    username,
    password,
  };

  if (uuid && captcha) {
    payload.uuid = uuid;
    payload.captcha = captcha;
  }

  return payload;
}

function normalizeAuthError(error: unknown): AuthError {
  if (isAxiosError<ErrorResponse>(error)) {
    const data = error.response?.data;
    const message = data?.msg || data?.message || error.message || DEFAULT_LOGIN_ERROR;
    return createAuthError(message, data?.code);
  }

  if (error instanceof Error) {
    return createAuthError(error.message || DEFAULT_LOGIN_ERROR, (error as AuthError).code);
  }

  return createAuthError(DEFAULT_LOGIN_ERROR);
}

function loginRedirectTarget(redirect: unknown): string {
  if (typeof redirect !== "string" || !redirect.startsWith("/") || redirect.startsWith("//")) {
    return "/dashboard";
  }

  if (typeof window !== "undefined") {
    const target = new URL(redirect, window.location.origin);
    if (target.origin !== window.location.origin) {
      return "/dashboard";
    }
  }

  return redirect;
}

export function useAuth() {
  const router = useRouter();
  const { axiosInstance } = useAxios();

  const authStore = useAuthStore(pinia);
  const loading = ref(false);

  function reloadAfterLogin() {
    const redirect = router.currentRoute.value.query.redirect;
    const target = loginRedirectTarget(redirect);

    if (typeof window !== "undefined") {
      window.location.assign(router.resolve(target).href);
      return;
    }
    void router.push(target);
  }

  function logout() {
    // TODO: 调用后端logout接口
    authStore.clearAuthInfo();
    void router.push({ path: "/auth/sign-in" });
  }

  async function login(username: string, password: string, uuid?: string, captcha?: string) {
    loading.value = true;
    try {
      const payload = buildLoginPayload(username, password, uuid, captcha);
      const response = await axiosInstance.post<LoginResponse>("/auth/login", payload);

      // 后端返回格式: { code: 200, msg: 'success', data: { access_token, access_token_expire_time, session_uuid, user } }
      const { code, data, msg } = response.data;
      if (code !== LOGIN_SUCCESS_CODE || !data) {
        throw createAuthError(msg || DEFAULT_LOGIN_ERROR, code);
      }

      // 存储认证信息到store
      authStore.setAuthInfo(data.access_token, data.session_uuid, data.user);
    } catch (error: unknown) {
      console.error("Login error:", error);
      const authError = normalizeAuthError(error);
      if (authError.code === CAPTCHA_ERROR_CODE) {
        toast.error(authError.message);
      }
      throw authError;
    } finally {
      loading.value = false;
    }

    reloadAfterLogin();
  }

  return {
    loading,
    logout,
    login,
  };
}
