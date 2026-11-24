interface ChildRenderOptions {
  el: HTMLElement
  signal?: AbortSignal
}

interface ResolvedWidget {
  render(opts: ChildRenderOptions): Promise<void>
}

interface Host {
  getWidget(ref: string): Promise<ResolvedWidget>
}

interface Model {
  get(key: string): unknown
  on(event: string, callback: () => void): void
  off(event: string, callback: () => void): void
}

export interface ComposeContext {
  model: Model
  host?: Host
  signal?: AbortSignal
}

const STATUS_STYLE =
  "margin-top:6px;padding:4px 8px;border-radius:4px;font:12px system-ui;" +
  "color:#991b1b;background:#fef2f2;border:1px solid #fecaca"

/**
 * Render the wrapped target into `slot`, and keep `status` showing the latest
 * problem: a failed save from Python, or a target that could not be shown.
 * `status` stays hidden while there is nothing to report.
 *
 * Returns a function that stops the status updates.
 */
export function showTargetAndStatus(
  ctx: ComposeContext,
  slot: HTMLElement,
  status: HTMLElement,
): () => void {
  status.style.cssText = STATUS_STYLE

  let renderError = ""
  const draw = () => {
    const text = renderError || (ctx.model.get("error") as string)
    status.textContent = text
    status.hidden = !text
  }
  ctx.model.on("change:error", draw)
  draw()

  const showTarget = async () => {
    try {
      if (!ctx.host) {
        throw new Error("this notebook cannot show a widget inside a widget")
      }
      const child = await ctx.host.getWidget(ctx.model.get("target") as string)
      await child.render({ el: slot, signal: ctx.signal })
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error)
      renderError = `Could not show the widget: ${reason}`
      draw()
    }
  }
  void showTarget()

  return () => ctx.model.off("change:error", draw)
}
