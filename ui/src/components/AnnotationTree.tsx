/** The annotation tree for one clip — the thing you open a clip to see.
 *
 * It renders whatever exists and says plainly when a branch is empty, because
 * an empty branch is information: it means that pass has not run yet.
 *
 * Hand assignment is shown only when the annotation states it. A blank
 * left/right is left blank on purpose — the agent is forbidden from guessing
 * it, and the UI must not paper over the gap.
 */

import { DASH, durationLabel, timecode } from "../lib/format";
import type { Annotation, Clip } from "../lib/types";
import { Pill } from "./primitives";

function Leaf({ label, children }: { label: string; children: React.ReactNode }) {
  if (children === null || children === undefined || children === "") return null;
  return (
    <div className="tree__leaf">
      <span>
        <b>{label}</b> {children}
      </span>
    </div>
  );
}

function Span({ annotation }: { annotation: Annotation }) {
  if (annotation.span_start === null && annotation.span_end === null) {
    return <span className="tree__span">{annotation.ref ?? "span"}</span>;
  }
  return (
    <span className="tree__span">
      {timecode(annotation.span_start)}–{timecode(annotation.span_end)}
    </span>
  );
}

function Tags({ tags }: { tags: string[] }) {
  if (!tags.length) return null;
  return (
    <div className="tree__tags">
      {tags.map((tag) => (
        <span className="tree__tag" key={tag}>
          {tag}
        </span>
      ))}
    </div>
  );
}

function AnnotationNode({
  annotation,
  children,
}: {
  annotation: Annotation;
  children?: React.ReactNode;
}) {
  const hands = [
    annotation.left_hand ? `left: ${annotation.left_hand}` : null,
    annotation.right_hand ? `right: ${annotation.right_hand}` : null,
  ].filter(Boolean) as string[];

  return (
    <div className="tree__node">
      <div className="tree__leaf">
        {annotation.hier_level ? (
          <span className="tree__level">{annotation.hier_level}</span>
        ) : null}
        <Span annotation={annotation} />
        {annotation.label ? <b>{annotation.label}</b> : null}
        {annotation.confidence !== null && annotation.confidence !== undefined ? (
          <Pill tone="muted">{annotation.confidence.toFixed(2)}</Pill>
        ) : null}
      </div>
      {annotation.narration ? (
        <div className="tree__leaf">
          <span className="tree__narration">{annotation.narration}</span>
        </div>
      ) : null}
      {hands.length ? <Leaf label="hands">{hands.join(" · ")}</Leaf> : null}
      {!hands.length && annotation.hier_level === "action" ? (
        // Only actions are expected to name a hand. Saying it at the task or
        // event level would read as a gap where there is none — but at the
        // action level the gap is real and has to be visible, because the agent
        // is forbidden from guessing.
        <div className="tree__leaf">
          <span className="tree__empty">hand assignment not stated in the captions</span>
        </div>
      ) : null}
      {annotation.objects.length ? <Leaf label="objects">{annotation.objects.join(", ")}</Leaf> : null}
      <Tags tags={annotation.tags} />
      {children}
    </div>
  );
}

/** Group a flat annotation list back into task → action → event. */
function hierarchy(annotations: Annotation[]) {
  const tasks = annotations.filter((a) => a.hier_level === "task");
  const actions = annotations.filter((a) => a.hier_level === "action");
  const events = annotations.filter((a) => a.hier_level === "event");
  const flat = annotations.filter((a) => !a.hier_level);
  return { tasks, actions, events, flat };
}

export function AnnotationTree({ clip }: { clip: Clip }) {
  const annotations = clip.annotations ?? [];
  const { tasks, actions, events, flat } = hierarchy(annotations);
  const childrenOf = (id: string | null) =>
    events.filter((event) => event.parent_segment_id === id);

  return (
    <div className="tree">
      <div>
        <span className="tree__branch">source</span>
        <div className="tree__node">
          <Leaf label="platform">{clip.platform}</Leaf>
          <Leaf label="creator">{clip.creator ?? ""}</Leaf>
          <Leaf label="length">{durationLabel(clip)}</Leaf>
          <Leaf label="licence">
            {clip.license ?? "unknown"}
            {clip.commercial_use_ok ? " · commercial use ok" : ""}
          </Leaf>
          <Leaf label="datalake id">{clip.datalake_video_id ?? ""}</Leaf>
        </div>
      </div>

      <div>
        <span className="tree__branch">viewpoint</span>
        <div className="tree__node">
          <Leaf label="verdict">
            {clip.viewpoint} ({clip.viewpoint_confidence.toFixed(2)})
          </Leaf>
          {clip.viewpoint_evidence.length ? (
            <Tags tags={clip.viewpoint_evidence} />
          ) : (
            <span className="tree__empty">no viewpoint cues in the available text</span>
          )}
        </div>
      </div>

      {clip.quality_grade || clip.annotation_level ? (
        <div>
          <span className="tree__branch">quality</span>
          <div className="tree__node">
            <Leaf label="grade">
              {clip.quality_grade ?? DASH}
              {clip.quality_score !== null && clip.quality_score !== undefined
                ? ` (${clip.quality_score}/100)`
                : ""}
            </Leaf>
            <Leaf label="annotation depth">{clip.annotation_level ?? DASH}</Leaf>
            <Leaf label="usable">
              {clip.usable_seconds !== null && clip.usable_seconds !== undefined
                ? `${timecode(clip.usable_seconds)} of ${durationLabel(clip)}`
                : ""}
            </Leaf>
            <Leaf label="task family">{clip.task_family ?? ""}</Leaf>
            {clip.blocking_failures?.length ? (
              <Leaf label="blocked by">{clip.blocking_failures.join(", ")}</Leaf>
            ) : null}
          </div>
        </div>
      ) : null}

      <div>
        <span className="tree__branch">annotation</span>
        {!annotations.length ? (
          <div className="tree__node">
            <span className="tree__empty">
              not annotated yet — index this clip and run the cleaning and annotation agents
            </span>
          </div>
        ) : (
          <div className="tree__node">
            {tasks.map((task) => (
              <AnnotationNode annotation={task} key={task.segment_id ?? "task"}>
                {actions
                  .filter((action) => action.parent_segment_id === task.segment_id)
                  .map((action) => (
                    <AnnotationNode annotation={action} key={action.segment_id ?? action.ref}>
                      {childrenOf(action.segment_id).map((event) => (
                        <AnnotationNode annotation={event} key={event.segment_id ?? event.ref} />
                      ))}
                    </AnnotationNode>
                  ))}
              </AnnotationNode>
            ))}
            {/* Actions whose task never came back still have to be shown. */}
            {actions
              .filter((action) => !tasks.some((task) => task.segment_id === action.parent_segment_id))
              .map((action) => (
                <AnnotationNode annotation={action} key={action.segment_id ?? action.ref}>
                  {childrenOf(action.segment_id).map((event) => (
                    <AnnotationNode annotation={event} key={event.segment_id ?? event.ref} />
                  ))}
                </AnnotationNode>
              ))}
            {flat.map((annotation, index) => (
              <AnnotationNode annotation={annotation} key={annotation.ref ?? index} />
            ))}
          </div>
        )}
      </div>

      {annotations.find((a) => a.caveat) ? (
        <p className="tree__caveat">
          {annotations.find((a) => a.caveat)?.caveat}
        </p>
      ) : null}
    </div>
  );
}

/** The same tree, for a clip that only exists as an ingest/curation result. */
export function AnnotationTreeFor({
  annotations,
  caveat,
}: {
  annotations: Annotation[];
  caveat?: string | null;
}) {
  const { tasks, actions, events, flat } = hierarchy(annotations);
  const childrenOf = (id: string | null) =>
    events.filter((event) => event.parent_segment_id === id);

  if (!annotations.length) {
    return <span className="tree__empty">no annotations written for this clip</span>;
  }

  return (
    <div className="tree">
      <div className="tree__node">
        {tasks.map((task) => (
          <AnnotationNode annotation={task} key={task.segment_id ?? "task"}>
            {actions
              .filter((action) => action.parent_segment_id === task.segment_id)
              .map((action) => (
                <AnnotationNode annotation={action} key={action.segment_id ?? action.ref}>
                  {childrenOf(action.segment_id).map((event) => (
                    <AnnotationNode annotation={event} key={event.segment_id ?? event.ref} />
                  ))}
                </AnnotationNode>
              ))}
          </AnnotationNode>
        ))}
        {actions
          .filter((action) => !tasks.some((task) => task.segment_id === action.parent_segment_id))
          .map((action) => (
            <AnnotationNode annotation={action} key={action.segment_id ?? action.ref} />
          ))}
        {flat.map((annotation, index) => (
          <AnnotationNode annotation={annotation} key={annotation.ref ?? index} />
        ))}
      </div>
      {caveat ? <p className="tree__caveat">{caveat}</p> : null}
    </div>
  );
}
