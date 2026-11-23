import { type ComposeContext, showTargetAndStatus } from "./compose"

export default {
  render(ctx: ComposeContext & { el: HTMLElement }) {
    const slot = document.createElement("div")
    const status = document.createElement("div")
    ctx.el.replaceChildren(slot, status)
    return showTargetAndStatus(ctx, slot, status)
  },
}
