/** The payload shapes the API actually sends, as the UI reads them.
 *
 * These mirror the server's models — `models/dataset.py`, `models/result.py`,
 * `pipeline/ingest.py` and the curation agent's `as_dict` — and nothing else.
 * A field that the server marks optional is optional here too: rendering a
 * missing number as `0` is how a clip nobody measured starts reading as a clip
 * that scored zero.
 */

/** One annotated span inside a clip: task, action or event. */
export interface Annotation {
  span_start: number | null;
  span_end: number | null;
  ref: string | null;

  segment_id: string | null;
  /** The span this one sits inside; null at the task level. */
  parent_segment_id: string | null;
  /** "task", "action" or "event". */
  hier_level: string | null;
  narration: string | null;

  label: string | null;
  /** What each hand does, only when the annotation states it. */
  left_hand: string | null;
  right_hand: string | null;
  objects: string[];
  tags: string[];

  source: string | null;
  confidence: number | null;
  caveat: string | null;
}

/** A candidate clip.
 *
 * One type for both `video_references` (what the search returned) and
 * `dataset.clips` (what the manifest carries), because the search view renders
 * whichever of the two it has for a URL. The fields only one of them sets are
 * optional.
 */
export interface Clip {
  url: string;
  platform: string;
  video_id?: string;
  title?: string | null;
  creator?: string | null;
  thumbnail_url?: string | null;
  relevance_note?: string | null;

  duration?: string | null;
  duration_seconds?: number | null;
  published_at?: string | null;

  viewpoint: string;
  viewpoint_confidence: number;
  viewpoint_evidence: string[];
  license?: string | null;
  usability_score: number;

  datalake_video_id?: string | null;
  annotations?: Annotation[];

  commercial_use_ok?: boolean;
  quality_score?: number | null;
  quality_grade?: string | null;
  annotation_level?: string | null;
  usable_seconds?: number | null;
  idle_seconds?: number | null;
  task_family?: string | null;
  dup_group_id?: string | null;
  blocking_failures?: string[];
}

/** The four hour measures, never mixed. */
export interface HoursLedger {
  worn_hours: number;
  delivered_hours: number;
  accepted_hours: number;
  accepted_labeled_hours: number;
  idle_hours: number;
  /** accepted / delivered — how much of the download survived. */
  media_yield: number;
}

export interface CostBreakdown {
  hours: number;
  discovery_usd: number;
  download_usd: number;
  indexing_usd: number;
  annotation_usd: number;
  storage_usd_per_month: number;
  total_usd: number;
  usd_per_collected_hour: number;
  usd_per_delivered_hour: number;
  assumed_yield: number;
  notes: string[];
}

/** One of the footage-shaped searches the request was rewritten into. */
export interface SearchRun {
  text: string;
  angle?: string | null;
}

/** Everything a collection run gathered, with its totals. */
export interface Manifest {
  query: string;
  requested_viewpoint?: string | null;
  target_hours?: number | null;

  total_clips: number;
  /** Delivered hours: every clip kept, before the media gates. */
  total_hours: number;
  clips_with_known_duration: number;

  hours: HoursLedger;
  accepted_clips: number;
  grades: Record<string, number>;
  annotation_levels: Record<string, number>;

  by_viewpoint: Record<string, number>;
  by_platform: Record<string, number>;
  reusable_license_clips: number;

  excluded_clips: number;
  exclusion_reasons: Record<string, number>;
  searches_run?: SearchRun[];

  cost?: CostBreakdown | null;
  clips: Clip[];
}

/** What the agent answered, and the dataset it built answering it. */
export interface AgentResponse {
  session_id: string;
  query: string;
  answer?: string;
  video_references?: Clip[];
  dataset?: Manifest | null;
  platforms_searched?: string[];
  total_videos_analyzed: number;
  steps_taken: number;
  tools_used?: string[];
  execution_time_seconds: number;
  usage_metrics?: Record<string, unknown> | null;
  needs_clarification?: boolean;
  clarification_question?: string | null;
}

/** One line in the activity log — the agent's own account of the run. */
export interface ActivityEntry {
  id: number;
  kind: string;
  message: string;
  failed?: boolean;
}

/** One quality-gate verdict.
 *
 * `measured` is not `passed`: a check nobody could run is excluded from the
 * score rather than assumed to have passed, and it has to render as its own
 * third state.
 */
export interface GateCheck {
  id: string;
  name: string;
  passed: boolean;
  measured: boolean;
  blocking: boolean;
  value?: string | number | boolean | null;
  threshold?: string | null;
  detail?: string | null;
}

/** What the pre-download look saw in the frames. */
export interface SightVerdict {
  viewpoint?: string | null;
  hands_visible?: boolean | null;
  confidence?: number | null;
  why?: string | null;
  method?: string | null;
  frames_seen?: number | null;
  cost_usd?: number | null;
  error?: string | null;
}

/** The metadata screen, before anything was spent on the clip. */
export interface Screening {
  accepted: boolean;
  reasons: string[];
  viewpoint?: string | null;
  commercial_use_ok?: boolean;
  notes: string[];
  sight?: SightVerdict | null;
  checks?: GateCheck[];
}

/** The scorecard for one clip, after the gates ran over the real media. */
export interface QualityReport {
  score: number;
  grade: string;
  accepted: boolean;
  commercial_use_ok: boolean;
  annotation_level?: string | null;
  usable_seconds?: number | null;
  idle_seconds?: number | null;
  blocking_failures: string[];
  unmeasured: string[];
  notes: string[];
  checks: GateCheck[];
}

export interface FrameCheck {
  hands_visible: boolean;
  hands_confidence?: number | null;
  hand_evidence?: string[];
  viewpoint?: string | null;
  is_footage?: boolean;
}

/** An anchor the cleaning agent cut, before anything labelled it. */
export interface CleanSegment {
  segment_id: string;
  parent_segment_id: string | null;
  hier_level: string;
  span_start: number | null;
  span_end: number | null;
  duration?: number | null;
  label: string | null;
  hands_visible?: boolean | null;
  evidence: string[];
}

/** The annotation pass over one clip. */
export interface AnnotationRun {
  annotations: Annotation[];
  survival_rate: number;
  annotation_level?: string | null;
  task_family?: string | null;
  tags_written?: string[];
  errors?: string[];
  caveat?: string | null;
}

/** One candidate's journey through the pipeline, as it streams. */
export interface IngestClip {
  url: string;
  /** probing → looking → downloading → uploading → indexing → cleaning →
   *  annotating, or a terminal accepted/rejected/skipped/failed/pending. */
  stage: string;
  accepted: boolean;

  video_id?: string | null;
  duration_seconds?: number | null;
  size_mb?: number | null;
  title?: string | null;
  tags_written: string[];

  rejection_reason?: string | null;
  /** Stopped without a verdict — indexed, but not judged. Not a rejection. */
  pending_reason?: string | null;
  error?: string | null;
  notes: string[];
  annotation_level?: string | null;

  screening?: Screening | null;
  quality?: QualityReport | null;
  frame_check?: FrameCheck | null;
  segments?: CleanSegment[];
  annotation?: AnnotationRun | null;
}

/** One graded clip in a curation run. */
export interface CurationClip {
  video_id: string;
  accepted: boolean;
  rejection_reason?: string | null;
  grade?: string | null;
  score?: number | null;
  annotation_level?: string | null;
  duration_seconds?: number | null;
}

/** The batch verdict over a worklist that is already indexed. */
export interface CurationResult {
  query: string;
  clips: CurationClip[];
  hours: HoursLedger;
  accepted_clips: number;
  total_clips: number;
  batch_grade: string;
  grades: Record<string, number>;
  annotation_levels: Record<string, number>;
  trace: unknown[];
  errors: string[];
}
