const state = {
  mode: "users",
  selectedType: null,
  selectedId: null,
  selectedChannelId: null,
  feedEndpoint: null,
  feedTitle: "Messages",
  feedSubtitle: "No selection",
  lastMessageId: null,
  loadedMessages: 0,
  loadingMessages: false,
  hasMoreMessages: false,
};

const MESSAGE_PAGE_SIZE = 100;

const els = {
  summary: document.querySelector("#summary"),
  userMode: document.querySelector("#userMode"),
  guildMode: document.querySelector("#guildMode"),
  searchForm: document.querySelector("#searchForm"),
  searchInput: document.querySelector("#searchInput"),
  results: document.querySelector("#results"),
  emptyState: document.querySelector("#emptyState"),
  userView: document.querySelector("#userView"),
  guildView: document.querySelector("#guildView"),
  userAvatar: document.querySelector("#userAvatar"),
  userName: document.querySelector("#userName"),
  userMeta: document.querySelector("#userMeta"),
  userGuilds: document.querySelector("#userGuilds"),
  userHistory: document.querySelector("#userHistory"),
  guildIcon: document.querySelector("#guildIcon"),
  guildName: document.querySelector("#guildName"),
  guildMeta: document.querySelector("#guildMeta"),
  guildChannels: document.querySelector("#guildChannels"),
  guildHistory: document.querySelector("#guildHistory"),
  messageTitle: document.querySelector("#messageTitle"),
  messageSubtitle: document.querySelector("#messageSubtitle"),
  messageStatus: document.querySelector("#messageStatus"),
  messages: document.querySelector("#messages"),
};

boot();

function boot() {
  els.userMode.addEventListener("click", () => setMode("users"));
  els.guildMode.addEventListener("click", () => setMode("guilds"));
  els.searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    runSearch();
  });
  els.messages.addEventListener("scroll", () => {
    if (
      state.hasMoreMessages &&
      !state.loadingMessages &&
      els.messages.scrollTop + els.messages.clientHeight >= els.messages.scrollHeight - 260
    ) {
      loadMoreMessages();
    }
  });

  loadSummary();
  runSearch();
}

async function loadSummary() {
  try {
    const summary = await api("/api/summary");
    els.summary.textContent = `${formatNumber(summary.users)} users, ${formatNumber(
      summary.guilds,
    )} guilds, ${formatNumber(summary.messages)} messages, ${formatNumber(summary.media)} media links`;
  } catch {
    els.summary.textContent = "Archive summary unavailable";
  }
}

function setMode(mode) {
  state.mode = mode;
  els.userMode.classList.toggle("active", mode === "users");
  els.guildMode.classList.toggle("active", mode === "guilds");
  els.searchInput.placeholder =
    mode === "users" ? "Search username or user ID" : "Search guild name or ID";
  runSearch();
}

async function runSearch() {
  const q = els.searchInput.value.trim();
  const endpoint = state.mode === "users" ? "/users" : "/guilds";
  setLoading(els.results, "Searching");

  try {
    const rows = await api(`${endpoint}?q=${encodeURIComponent(q)}&limit=50`);
    renderResults(rows);
  } catch (error) {
    renderError(els.results, error);
  }
}

function renderResults(rows) {
  els.results.replaceChildren();

  if (!rows.length) {
    els.results.appendChild(emptyLine("No matches"));
    return;
  }

  for (const row of rows) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "result-row";
    button.addEventListener("click", () => {
      if (state.mode === "users") {
        selectUser(row.id);
      } else {
        selectGuild(row.id);
      }
    });

    button.appendChild(avatar(resultImage(row)));
    button.appendChild(
      rowText(
        state.mode === "users" ? displayUser(row) : row.name || row.id,
        `${row.id} · last seen ${formatDate(row.last_seen || row.last_scraped)}`,
      ),
    );
    els.results.appendChild(button);
  }
}

async function selectUser(userId) {
  state.selectedType = "user";
  state.selectedId = userId;
  state.selectedChannelId = null;
  showView("user");
  setLoading(els.userGuilds, "Loading servers");
  setLoading(els.userHistory, "Loading history");
  setLoading(els.messages, "Loading messages");

  try {
    const [user, guilds, history] = await Promise.all([
      api(`/users/${userId}`),
      api(`/users/${userId}/guilds`),
      api(`/users/${userId}/history`),
    ]);

    setImage(
      els.userAvatar,
      user.display_avatar_url || preferredImage(user.avatar_cache_url, user.avatar_url),
    );
    els.userName.textContent = displayUser(user);
    els.userMeta.textContent = `${user.id} · first seen ${formatDate(user.first_seen)} · last seen ${formatDate(
      user.last_seen,
    )}`;
    renderUserGuilds(guilds);
    renderUserHistory(history);
    await startMessageFeed(`/users/${userId}/messages`, "User Messages", "Newest messages");
  } catch (error) {
    renderError(els.messages, error);
  }
}

async function selectGuild(guildId) {
  state.selectedType = "guild";
  state.selectedId = guildId;
  state.selectedChannelId = null;
  showView("guild");
  setLoading(els.guildChannels, "Loading channels");
  setLoading(els.guildHistory, "Loading history");
  setLoading(els.messages, "Loading messages");

  try {
    const [guild, channels, history] = await Promise.all([
      api(`/guilds/${guildId}`),
      api(`/guilds/${guildId}/channels`),
      api(`/guilds/${guildId}/history`),
    ]);

    setImage(els.guildIcon, preferredImage(guild.icon_cache_url, guild.icon_url));
    els.guildName.textContent = guild.name || guild.id;
    els.guildMeta.textContent = `${guild.id} · first seen ${formatDate(
      guild.first_seen,
    )} · last scraped ${formatDate(guild.last_scraped)}`;
    renderGuildChannels(channels);
    renderGuildHistory(history);
    await startMessageFeed(`/guilds/${guildId}/messages`, "Guild Messages", "Newest messages across all channels");
  } catch (error) {
    renderError(els.messages, error);
  }
}

function renderUserGuilds(guilds) {
  els.userGuilds.replaceChildren();
  if (!guilds.length) {
    els.userGuilds.appendChild(emptyLine("No shared guilds recorded"));
    return;
  }

  for (const guild of guilds) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "compact-row";
    row.addEventListener("click", () => selectGuild(guild.id));
    row.appendChild(avatar(preferredImage(guild.icon_cache_url, guild.icon_url)));
    row.appendChild(rowText(guild.name || guild.id, `last seen ${formatDate(guild.last_seen)}`));
    els.userGuilds.appendChild(row);
  }
}

function renderUserHistory(history) {
  els.userHistory.replaceChildren();
  if (!history.length) {
    els.userHistory.appendChild(emptyLine("No profile changes recorded"));
    return;
  }

  for (const item of history) {
    els.userHistory.appendChild(
      historyRow(
        item.display_avatar_url || preferredImage(item.avatar_cache_url, item.avatar_url),
        displayUser(item),
        `${formatDate(item.seen_at)} · avatar ${item.avatar || "none"}`,
      ),
    );
  }
}

function renderGuildChannels(channels) {
  els.guildChannels.replaceChildren();
  if (!channels.length) {
    els.guildChannels.appendChild(emptyLine("No channels recorded yet"));
    return;
  }

  const all = document.createElement("button");
  all.type = "button";
  all.className = "compact-row";
  all.addEventListener("click", () => {
    state.selectedChannelId = null;
    startMessageFeed(`/guilds/${state.selectedId}/messages`, "Guild Messages", "Newest messages across all channels");
  });
  all.appendChild(channelBadge("All"));
  all.appendChild(rowText("All channels", `${channels.reduce((sum, c) => sum + c.message_count, 0)} messages`));
  els.guildChannels.appendChild(all);

  for (const channel of channels) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "compact-row";
    row.addEventListener("click", () => {
      state.selectedChannelId = channel.id;
      startMessageFeed(
        `/guilds/${state.selectedId}/channels/${channel.id}/messages`,
        `#${channel.name || channel.id}`,
        "Newest messages",
      );
    });
    row.appendChild(channelBadge("#"));
    row.appendChild(
      rowText(
        channel.name || channel.id,
        `${formatNumber(channel.message_count)} messages · last ${formatDate(channel.last_message_at)}`,
      ),
    );
    els.guildChannels.appendChild(row);
  }
}

function renderGuildHistory(history) {
  els.guildHistory.replaceChildren();
  if (!history.length) {
    els.guildHistory.appendChild(emptyLine("No guild changes recorded"));
    return;
  }

  for (const item of history) {
    els.guildHistory.appendChild(
      historyRow(
        preferredImage(item.icon_cache_url, item.icon_url),
        item.name || "Unnamed guild",
        `${formatDate(item.seen_at)} · icon ${item.icon || "none"}`,
      ),
    );
  }
}

async function startMessageFeed(endpoint, title, subtitle) {
  state.feedEndpoint = endpoint;
  state.feedTitle = title;
  state.feedSubtitle = subtitle;
  state.lastMessageId = null;
  state.loadedMessages = 0;
  state.hasMoreMessages = true;
  els.messages.replaceChildren();
  els.messages.scrollTop = 0;
  els.messageTitle.textContent = title;
  els.messageSubtitle.textContent = subtitle;
  await loadMoreMessages();
}

async function loadMoreMessages() {
  if (!state.feedEndpoint || state.loadingMessages || !state.hasMoreMessages) {
    return;
  }

  state.loadingMessages = true;
  updateMessageStatus("Loading");

  const params = new URLSearchParams({ limit: String(MESSAGE_PAGE_SIZE) });
  if (state.lastMessageId) {
    params.set("before", state.lastMessageId);
  }

  try {
    const messages = await api(`${state.feedEndpoint}?${params.toString()}`);
    appendMessages(messages);

    if (messages.length) {
      state.lastMessageId = messages[messages.length - 1].id;
      state.loadedMessages += messages.length;
    }
    state.hasMoreMessages = messages.length === MESSAGE_PAGE_SIZE;

    els.messageSubtitle.textContent = `${state.feedSubtitle} · ${formatNumber(
      state.loadedMessages,
    )} loaded`;
    updateMessageStatus(state.hasMoreMessages ? "Scroll for more" : "End");
  } catch (error) {
    renderError(els.messages, error);
    updateMessageStatus("Error");
  } finally {
    state.loadingMessages = false;
  }

  if (
    state.hasMoreMessages &&
    !state.loadingMessages &&
    els.messages.scrollHeight <= els.messages.clientHeight
  ) {
    setTimeout(() => loadMoreMessages(), 0);
  }
}

function appendMessages(messages) {
  if (!messages.length) {
    if (!state.loadedMessages) {
      els.messages.appendChild(emptyLine("No messages found"));
    }
    return;
  }

  for (const message of messages) {
    const row = document.createElement("article");
    row.className = "message-row";

    const meta = document.createElement("div");
    meta.className = "message-meta";
    const author = message.username ? `${message.username} (${message.user_id}) · ` : "";
    meta.textContent = `${author}${message.guild_name || message.guild_id} / #${
      message.channel_name || message.channel_id
    } · ${formatDate(message.created_at)} · ${message.id}`;
    row.appendChild(meta);

    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = message.content || "";
    row.appendChild(content);

    if (message.media?.length) {
      const media = document.createElement("div");
      media.className = "media-list";
      for (const item of message.media) {
        const link = document.createElement("a");
        link.className = "media-link";
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = item.filename || item.kind || "media";
        media.appendChild(link);
      }
      row.appendChild(media);
    }

    els.messages.appendChild(row);
  }
}

function showView(view) {
  els.emptyState.classList.add("hidden");
  els.userView.classList.toggle("hidden", view !== "user");
  els.guildView.classList.toggle("hidden", view !== "guild");
}

async function api(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function rowText(title, meta) {
  const wrap = document.createElement("div");
  const titleEl = document.createElement("div");
  const metaEl = document.createElement("div");
  titleEl.className = "row-title";
  metaEl.className = "row-meta";
  titleEl.textContent = title || "Unknown";
  metaEl.textContent = meta || "";
  wrap.append(titleEl, metaEl);
  return wrap;
}

function historyRow(imageUrl, title, meta) {
  const row = document.createElement("div");
  row.className = "history-row";
  row.appendChild(avatar(imageUrl));
  row.appendChild(rowText(title, meta));
  return row;
}

function avatar(src) {
  const img = document.createElement("img");
  img.className = "avatar";
  img.alt = "";
  setImage(img, src);
  return img;
}

function setImage(img, src) {
  const normalized = normalizeImageUrl(src);
  if (normalized) {
    img.src = normalized;
  } else {
    img.removeAttribute("src");
  }
}

function preferredImage(cacheUrl, remoteUrl) {
  return cacheUrl || normalizeImageUrl(remoteUrl);
}

function resultImage(row) {
  if (state.mode === "users") {
    return (
      row.display_avatar_url ||
      row.default_avatar_url ||
      preferredImage(row.avatar_cache_url, row.avatar_url)
    );
  }

  return preferredImage(row.icon_cache_url, row.icon_url);
}

function normalizeImageUrl(url) {
  if (!url) {
    return null;
  }

  if (url.includes("/embed/avatars/")) {
    return url;
  }

  const [base, query = ""] = url.split("?");
  const webpBase = base.replace(/\.(png|jpg|jpeg|gif)(?=$|[?#])/i, ".webp");
  return query ? `${webpBase}?${query}` : webpBase;
}

function updateMessageStatus(text) {
  els.messageStatus.textContent = text;
}

function channelBadge(text) {
  const badge = document.createElement("span");
  badge.className = "pill";
  badge.textContent = text;
  return badge;
}

function emptyLine(text) {
  const div = document.createElement("div");
  div.className = "message-row";
  div.textContent = text;
  return div;
}

function setLoading(parent, text) {
  parent.replaceChildren(emptyLine(text));
}

function renderError(parent, error) {
  parent.replaceChildren(emptyLine(`Error: ${error.message}`));
}

function displayUser(user) {
  const name = user.username || "Unknown user";
  return user.discriminator && user.discriminator !== "0"
    ? `${name}#${user.discriminator}`
    : name;
}

function formatDate(value) {
  if (!value) {
    return "unknown";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(value || 0);
}
