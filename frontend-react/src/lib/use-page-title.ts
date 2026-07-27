import { useEffect } from "react"
import { BRAND, getDocumentTitle } from "@/lib/brand"

export function usePageTitle(path: string, custom?: string) {
  useEffect(() => {
    document.title = getDocumentTitle(path, custom)

    const description =
      document.querySelector("meta[name='description']") ??
      document.querySelector("meta[property='og:description']")
    if (description) {
      description.setAttribute("content", BRAND.description)
    }
  }, [path, custom])
}
