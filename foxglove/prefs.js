// Foxglove default preferences
// Targets Firefox 135+. Cross-referenced with arkenfox user.js v140.

// --- Startup & UI -----------------------------------------------------------

user_pref("browser.aboutConfig.showWarning", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.disableResetPrompt", true);
user_pref("browser.reader.detectedFirstArticle", true);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.blankWindow", true);
user_pref("browser.startup.couldRestoreSession.count", 2);
user_pref("browser.startup.homepage", "about:blank");
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.toolbarbuttons.introduced.pocket-button", true);
user_pref("browser.uitour.enabled", false);
user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);

// --- Telemetry & Data Reporting ---------------------------------------------

user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.coverage.endpoint.base", "");
user_pref("toolkit.coverage.opt-out", true);
user_pref("toolkit.telemetry.archive.enabled", false);
user_pref("toolkit.telemetry.bhrPing.enabled", false);
user_pref("toolkit.telemetry.coverage.opt-out", true);
user_pref("toolkit.telemetry.enabled", false);
user_pref("toolkit.telemetry.firstShutdownPing.enabled", false);
user_pref("toolkit.telemetry.newProfilePing.enabled", false);
user_pref("toolkit.telemetry.server", "data:,");
user_pref("toolkit.telemetry.shutdownPingSender.enabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.updatePing.enabled", false);

// --- Normandy / Shield / Studies --------------------------------------------

user_pref("app.normandy.api_url", "");
user_pref("app.normandy.enabled", false);
user_pref("app.shield.optoutstudies.enabled", false);

// --- Crash Reports ----------------------------------------------------------

user_pref("breakpad.reportURL", "");
user_pref("browser.crashReports.unsubmittedCheck.autoSubmit2", false);
user_pref("browser.crashReports.unsubmittedCheck.enabled", false);
user_pref("browser.tabs.crashReporting.sendReport", false);

// --- Captive Portal & Connectivity ------------------------------------------

user_pref("captivedetect.canonicalURL", "");
user_pref("network.captive-portal-service.enabled", false);
user_pref("network.connectivity-service.enabled", false);

// --- New Tab Page / Activity Stream -----------------------------------------

user_pref("browser.newtab.preload", false);
user_pref("browser.newtabpage.activity-stream.asrouter.disable-captive-portal-vpn-promo", true);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
user_pref("browser.newtabpage.activity-stream.default.sites", "");
user_pref("browser.newtabpage.activity-stream.feeds.section.highlights", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.section.highlights.includeBookmarks", false);
user_pref("browser.newtabpage.activity-stream.section.highlights.includeDownloads", false);
user_pref("browser.newtabpage.activity-stream.section.highlights.includePocket", false);
user_pref("browser.newtabpage.activity-stream.section.highlights.includeVisited", false);
user_pref("browser.newtabpage.activity-stream.showSearch", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredCheckboxes", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
user_pref("browser.newtabpage.enabled", false);

// --- VPN / Mozilla Promos ---------------------------------------------------

user_pref("browser.contentblocking.report.hide_vpn_banner", true);
user_pref("browser.contentblocking.report.vpn.url", "about:blank");
user_pref("browser.privatebrowsing.vpnpromourl", "about:blank");

// --- URL Bar / Search -------------------------------------------------------

user_pref("browser.search.separatePrivateDefault", true);
user_pref("browser.search.separatePrivateDefault.ui.enabled", true);
user_pref("browser.search.suggest.enabled", false);
user_pref("browser.urlbar.addons.featureGate", false);
user_pref("browser.urlbar.amp.featureGate", false);
user_pref("browser.urlbar.fakespot.featureGate", false);
user_pref("browser.urlbar.mdn.featureGate", false);
user_pref("browser.urlbar.quicksuggest.enabled", false);
user_pref("browser.urlbar.showSearchTerms.enabled", false);
user_pref("browser.urlbar.speculativeConnect.enabled", false);
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.sponsored", false);
user_pref("browser.urlbar.suggest.searches", false);
user_pref("browser.urlbar.trending.featureGate", false);
user_pref("browser.urlbar.trimURLs", false);
user_pref("browser.urlbar.weather.featureGate", false);
user_pref("browser.urlbar.wikipedia.featureGate", false);
user_pref("browser.urlbar.yelp.featureGate", false);
user_pref("keyword.enabled", false);

// --- Network / Prefetch / Speculative Loading -------------------------------

user_pref("browser.places.speculativeConnect.enabled", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.dns.disablePrefetchFromHTTPS", true);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("network.predictor.enable-prefetch", false);
user_pref("network.predictor.enabled", false);
user_pref("network.prefetch-next", false);

// --- Referer ----------------------------------------------------------------
// XOriginTrimmingPolicy=2: send only scheme+host+port for cross-origin requests.
// spoofSource MUST be false — spoofing breaks CSRF protections (arkenfox §6002).

user_pref("network.http.referer.spoofSource", false);
user_pref("network.http.referer.XOriginTrimmingPolicy", 2);

// --- Cookies / Enhanced Tracking Protection ---------------------------------
// cookieBehavior=5 is Total Cookie Protection (partitioned), the default with
// ETP Strict. Value 1 (block all 3rd-party) causes breakage.

user_pref("browser.contentblocking.category", "strict");
user_pref("network.cookie.cookieBehavior", 5);

// --- Privacy & Tracking Protection ------------------------------------------

user_pref("privacy.globalprivacycontrol.enabled", true);
user_pref("privacy.query_stripping.enabled", true);
user_pref("privacy.resistFingerprinting", false);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("privacy.trackingprotection.pbmode.enabled", true);
user_pref("privacy.userContext.enabled", true);
user_pref("privacy.userContext.ui.enabled", true);

// --- HTTPS / TLS / Certificates ---------------------------------------------

user_pref("dom.security.https_only_mode", true);
user_pref("dom.security.https_only_mode_send_http_background_request", false);
user_pref("security.cert_pinning.enforcement_level", 2);
user_pref("security.OCSP.require", true);
user_pref("security.pki.crlite_mode", 2);
user_pref("security.ssl.require_safe_negotiation", true);
user_pref("security.tls.enable_0rtt_data", false);

// --- DNS / DoH --------------------------------------------------------------

user_pref("doh-rollout.disable-heuristics", true);
user_pref("network.file.disable_unc_paths", true);
user_pref("network.proxy.socks_remote_dns", true);
user_pref("network.trr.mode", 0);

// --- Fingerprinting / DOM ---------------------------------------------------

user_pref("beacon.enabled", false);
user_pref("dom.battery.enabled", false);
user_pref("dom.disable_window_move_resize", true);
user_pref("dom.event.clipboardevents.enabled", false);
user_pref("geo.enabled", false);
user_pref("geo.provider.ms-windows-location", false);
user_pref("geo.provider.use_corelocation", false);
user_pref("geo.provider.use_geoclue", false);
user_pref("media.navigator.enabled", false);
user_pref("media.peerconnection.enabled", false);
user_pref("media.peerconnection.ice.default_address_only", true);
user_pref("media.peerconnection.ice.proxy_only_if_behind_proxy", true);
user_pref("media.video_stats.enabled", false);
user_pref("media.videocontrols.picture-in-picture.video-toggle.enabled", false);

// --- Extensions -------------------------------------------------------------

user_pref("browser.discovery.enabled", false);
user_pref("extensions.autoDisableScopes", 14);
user_pref("extensions.getAddons.cache.enabled", false);
user_pref("extensions.htmlaboutaddons.recommendations.enabled", false);
user_pref("extensions.pocket.enabled", false);
user_pref("extensions.recommendations.hideNotice", true);
user_pref("extensions.screenshots.upload-disabled", true);
user_pref("extensions.ui.lastCategory", "addons://list/extension");

// --- Downloads & Temp Files -------------------------------------------------

user_pref("browser.download.start_downloads_in_tmp_dir", true);
user_pref("browser.helperApps.deleteTempFileOnExit", true);

// --- Network Misc -----------------------------------------------------------

user_pref("browser.send_pings", false);
user_pref("network.IDN_show_punycode", true);

// --- PDF / Media ------------------------------------------------------------

user_pref("pdfjs.enableScripting", false);

// --- Developer Tools --------------------------------------------------------

user_pref("devtools.everOpened", true);
user_pref("devtools.netmonitor.persistlog", true);
user_pref("devtools.webconsole.persistlog", true);

// --- Misc UI ----------------------------------------------------------------

user_pref("browser.contentanalysis.enabled", false);
user_pref("layout.spellcheckDefault", 0);
user_pref("middlemouse.contentLoadURL", false);
user_pref("permissions.manager.defaultsUrl", "");
user_pref("print.more-settings.open", true);
