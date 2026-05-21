export enum NoticeType {
  Notice = 0,
  Announcement = 1,
}

export enum NoticeStatus {
  Hidden = 0,
  Visible = 1,
}

export interface Notice {
  id: number;
  title: string;
  type: NoticeType;
  status: NoticeStatus;
  content: string;
  created_time: string;
  updated_time: string | null;
}

export interface NoticePayload {
  title: string;
  type: NoticeType;
  status: NoticeStatus;
  content: string;
}

export interface NoticeListParams {
  page: number;
  size: number;
  title?: string;
  type?: number;
  status?: number;
}

export interface NoticeUpdatePayload {
  id: number;
  payload: NoticePayload;
}
