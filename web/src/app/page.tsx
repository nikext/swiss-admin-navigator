import { cookies, headers } from "next/headers";

import Chat from "@/components/Chat";
import Login from "@/components/Login";
import { pickLang } from "@/lib/i18n";
import { config } from "@/lib/server/config";
import { identify } from "@/lib/server/http";

export const dynamic = "force-dynamic";

export default async function Home() {
  const lang = pickLang(
    (await cookies()).get("nav_lang")?.value,
    (await headers()).get("accept-language"),
  );
  const id = await identify();
  if (!id) return <Login initialLang={lang} />;
  const c = config();
  return <Chat initialLang={lang} userQuota={c.userDailyQuota} />;
}
