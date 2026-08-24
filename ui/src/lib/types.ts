/** The shapes the API sends, as the UI reads them.
 *
 * These mirror the Pydantic models behind `/api/v1/*` rather than restating
 * them: a field that is optional here is one the server may omit, and a field
 * that is `| null` is one the server sends as an explicit null. The difference
 * matters in this codebase — a null hand is "not established", not "no hand",
 * and the tree renders the two differently.
 *
 * Reconstructed from the shipped bundle and the components' own usage after
 * `ui/src/lib/` was found missing from the repository; the components are the
 * authority for every field named here.
 */

/** One node of an annotation tree, on time anchors over a video. */
export interface Annotation {
  ref?: string | null;
  segment_id: string | null;
  parent_segment_id: string | null;
  hier_level?: string | null;
  span_start: number | null;
  span_end: number | null;
  label?: string | null;
  narration?: string | null;
  /** Left blank when the evidence does not name a hand. Never guessed. */
  left_hand?: string | null;
  right_hand?: string | null;
  objects: string[];
  tags: string[];
  confidence?: number | null;
  /** How the verdict was reached, e.g. read from captions rather than pixels. */
  caveat?: string | null;
}

/** One executable check from the quality standard.
 *
 * Three states, not two: an unmeasured check is a number nobody has, and is
 * excluded from the score rather than assumed to pass.
 */
export interface GateCheck {
  id: string;
  name: string;
  passed: boolean;
  measured: boolean;
  blocking: boolean;
  value?: string | number | null;
  threshold?: string | null;
  detail?: string | null;
}

/** A candidate or collected clip, as the search and manifest describe it. */
export interface Clip {
  url: string;
  platform: string;
  title?: string | null;
  creator?: string | null;
  thumbnail_url?: string | null;
  /** A pre-formatted length when the source gave one, e.g. "12:04". */
  duration?: string | null;
  duration_seconds?: number | null;
  viewpoint: string;
  viewpoint_confidence: number;
  viewpoint_evidence: string[];
  license?: string | null;
  commercial_use_ok?: boolean | null;
  usability_score: number;
  relevance_note?: string | null;
  datalake_video_id?: string | null;
  quality_grade?: string | null;
  quality_score?: number | null;
  annotation_level?: string | null;
  usable_seconds?: number | null;
  idle_seconds?: number | null;
  task_family?: string | null;
  dup_group_id?: string | null;
  blocking_failures?: string[] | null;
  annotations?: Annotation[] | null;
}

/** The four hour measures, kept apart on purpose.
 *
 * `delivered` is what landed on disk, `accepted` is what cleared Gate 0 and 1
 * with idle removed, and `accepted_labeled` is the only figure that may be
 * quoted externally.
 */
export interface HoursLedger {
  worn_hours?: number;
  delivered_hours: number;
  accepted_hours: number;
  accepted_labeled_hours: number;
  idle_hours: number;
  media_yield: number;
}

/** What an hour cost, from published rates plus what the run measured. */
export interface CostBreakdown {
  hours: number;
  discovery_usd: number;
  download_usd?: number;
  indexing_usd: number;
  annotation_usd?: number;
  storage_usd_per_month?: number;
  total_usd: number;
  usd_per_collected_hour: number;
  usd_per_delivered_hour: number;
  assumed_yield: number;
  /** Terms the run could not measure, named rather than filled with a guess. */
  notes: string[];
}

/** One search the agent actually ran, so the UI can show what was asked. */
export interface SearchRun {
  text: string;
  angle?: string;
  source?: string;
}

/** The dataset manifest a run emits: the clips, and what they add up to. */
export interface Manifest {
  query?: string;
  requested_viewpoint?: string | null;
  target_hours?: number | null;
  total_clips: number;
  total_hours: number;
  clips_with_known_duration?: number;
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

/** What one query returned. */
export interface AgentResponse {
  session_id?: string;
  answer: string;
  video_references: Clip[];
  dataset?: Manifest | null;
  steps_taken: number;
  total_videos_analyzed: number;
  execution_time_seconds: number;
}

/** What a frame check saw, before anything was downloaded. */
export interface SightVerdict {
  viewpoint: string;
  hands_visible?: boolean | null;
  confidence: number;
  why?: string;
  method?: string;
  frames_seen?: number;
  cost_usd?: number | null;
  error?: string | null;
}

/** The pre-download screen: what was checked, and what it concluded. */
export interface Screening {
  url?: string;
  accepted: boolean;
  reasons: string[];
  viewpoint?: string;
  viewpoint_confidence?: number;
  duration_seconds?: number | null;
  commercial_use_ok?: boolean | null;
  notes?: string[];
  sight?: SightVerdict | null;
  checks?: GateCheck[];
}

/** The cleaning agent's read of the frames it looked at. */
export interface FrameCheck {
  hands_visible?: boolean | null;
  hands_confidence?: number;
  hand_evidence?: string[];
  viewpoint?: string;
  is_footage?: boolean | null;
}

/** A clip's quality report: the score, the grade, and every check behind it. */
export interface QualityReport {
  score: number;
  grade: string;
  accepted: boolean;
  commercial_use_ok?: boolean;
  annotation_level?: string | null;
  usable_seconds?: number | null;
  idle_seconds?: number | null;
  blocking_failures: string[];
  unmeasured: string[];
  notes: string[];
  checks: GateCheck[];
}

/** One span the cleaning agent proposed, before it is labelled. */
export interface ProposedSegment {
  segment_id: string;
  parent_segment_id?: string | null;
  hier_level: string;
  span_start: number;
  span_end: number;
  duration?: number;
  label?: string | null;
  narration?: string | null;
  hands_visible?: boolean | null;
  evidence: string[];
}

/** What the annotation pass produced for one video. */
export interface AnnotationRun {
  annotations: Annotation[];
  survival_rate?: number | null;
  annotation_level?: string | null;
  task_family?: string | null;
  tags_written?: string[];
  caveat?: string | null;
  errors?: string[];
}

/** One clip's journey through collection, streamed a stage at a time. */
export interface IngestClip {
  url: string;
  stage: string;
  accepted: boolean;
  video_id?: string | null;
  duration_seconds?: number | null;
  size_mb?: number | null;
  title?: string | null;
  tags_written: string[];
  rejection_reason?: string | null;
  pending_reason?: string | null;
  error?: string | null;
  notes: string[];
  annotation_level?: string | null;
  screening?: Screening | null;
  cleaning?: unknown;
  frame_check?: FrameCheck | null;
  quality?: QualityReport | null;
  segments?: ProposedSegment[] | null;
  annotation?: AnnotationRun | null;
}

/** Where a curation pass's videos actually are, and what does not exist yet. */
export interface CurationStorage {
  kind: string;
  collection_id: string;
  collection_name: string;
  video_ids: string[];
  clips_cut: number;
  on_disk: boolean;
  note: string;
}

/** What grading a whole set concluded. */
export interface CurationResult {
  query?: string;
  clips: unknown[];
  hours: HoursLedger;
  accepted_clips: number;
  total_clips: number;
  batch_grade: string;
  grades: Record<string, number>;
  annotation_levels: Record<string, number>;
  errors: string[];
  storage?: CurationStorage | null;
}

/** One line in the live activity log. */
export interface ActivityEntry {
  /** A counter, not an identifier: it only has to be unique within one run. */
  id: number;
  kind: string;
  message: string;
  failed?: boolean;
}
