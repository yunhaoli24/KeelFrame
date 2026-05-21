export enum DictDataStatus {
  Disabled = 0,
  Enabled = 1,
}

export interface DictData {
  id: number;
  type_id: number;
  type_code: string;
  label: string;
  value: string;
  color: string | null;
  sort: number;
  status: DictDataStatus;
  remark: string | null;
  created_time: string;
  updated_time: string | null;
}

export interface DictDataPayload {
  type_id: number;
  label: string;
  value: string;
  color?: string | null;
  sort: number;
  status: DictDataStatus;
  remark?: string | null;
}

export interface DictDataListParams {
  page: number;
  size: number;
  type_code?: string;
  label?: string;
  value?: string;
  status?: number;
  type_id?: number;
}

export interface DictDataUpdatePayload {
  id: number;
  payload: DictDataPayload;
}
