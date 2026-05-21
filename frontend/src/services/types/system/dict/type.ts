export interface DictType {
  id: number;
  name: string;
  code: string;
  remark: string | null;
  created_time: string;
  updated_time: string | null;
}

export interface DictTypePayload {
  name: string;
  code: string;
  remark?: string | null;
}

export interface DictTypeListParams {
  page: number;
  size: number;
  name?: string;
  code?: string;
}

export interface DictTypeUpdatePayload {
  id: number;
  payload: DictTypePayload;
}
