#!/usr/bin/env python3
"""Brand a fixed, reconstructed open-source base as a separate TEAMMOD27 app.

This runs only in TEAMMOD27's build workspace. Never writes to RUIZEN.
Never alters the existing Apple-named bundle identifier requested by owner.
No pairing credentials, PINs or license secrets are incorporated.
"""
from pathlib import Path
import plistlib
import sys
import json
import re

ROOT = Path(sys.argv[1]).resolve()
ASSETS = ROOT / "ThreeOneOSFive/Assets.xcassets"
assert (ROOT / "ThreeOneOSFive.xcodeproj/project.pbxproj").is_file()

def replace_in(path, pairs):
    p = ROOT / path
    value = p.read_text(encoding="utf8")
    for old, new in pairs:
        value = value.replace(old, new)
    p.write_text(value, encoding="utf8")

info_path = ROOT / "ThreeOneOSFive/Info.plist"
info = plistlib.loads(info_path.read_bytes())
assert info.get("CFBundleIdentifier") == "com.apple.mobile.MobileHouseArrest", "Do not change original Bundle ID"
info.update({
    "CFBundleDisplayName": "TEAMMOD27",
    "CFBundleName": "TEAMMOD27",
    "CFBundleShortVersionString": "1.0.0",
    "CFBundleVersion": "1",
    "AppReleaseDisplayVersion": "1.0.0",
    "HTVLicenseBaseURL": "https://hightapi.netlify.app",
    "HTVLicenseAppID": "teammod27",
    "PatchServerBaseURL": "https://hightapi.netlify.app",
    "PatchCatalogURL": "https://hightapi.netlify.app/api/v4/packages",
    "NSLocalNetworkUsageDescription": "TEAMMOD27 uses the local network to pair with this iPhone and discover RSD services."
})
info_path.write_bytes(plistlib.dumps(info,fmt=plistlib.FMT_XML,sort_keys=False))

project = ROOT / "ThreeOneOSFive.xcodeproj/project.pbxproj"
pbx = project.read_text()
assert pbx.count('PRODUCT_BUNDLE_IDENTIFIER = "com.apple.mobile.MobileHouseArrest";') == 2
for old,new in [
    ('CURRENT_PROJECT_VERSION = 13;', 'CURRENT_PROJECT_VERSION = 1;'),
    ('MARKETING_VERSION = 1.1.6;', 'MARKETING_VERSION = 1.0.0;'),
    ('MARKETING_VERSION = 1.0.0;', 'MARKETING_VERSION = 1.0.0;'),
    ('INFOPLIST_KEY_CFBundleDisplayName = 3105;', 'INFOPLIST_KEY_CFBundleDisplayName = TEAMMOD27;'),
    ('PRODUCT_NAME = 3105;', 'PRODUCT_NAME = TEAMMOD27;'),
]:
    pbx = pbx.replace(old,new)
project.write_text(pbx)
assert pbx.count('PRODUCT_BUNDLE_IDENTIFIER = "com.apple.mobile.MobileHouseArrest";') == 2

source_root=ROOT/"ThreeOneOSFive"
for p in source_root.rglob("*"):
    if not p.is_file() or p.suffix not in {".swift",".m",".h",".strings"}: continue
    s=p.read_text("utf8",errors="replace")
    s=s.replace("htvantix.license.", "teammod27.license.")
    s=s.replace("htvantix.client.", "teammod27.client.")
    s=s.replace('"appId": "ruizenclient"', '"appId": "teammod27"')
    s=s.replace('"RUIZEN CLIENT"', '"TEAMMOD27"')
    s=s.replace('"RUIZEN-CLIENT"', '"TEAMMOD27"')
    s=s.replace("RUIZEN CLIENT", "TEAMMOD27")
    s=s.replace("VIPERX", "TEAMMOD27")
    p.write_text(s,encoding="utf8")
app=(source_root/"App.swift").read_text()
assert app.count('"appId": "teammod27"')==2, "License app ID wiring mismatch"
assert "hightapi.netlify.app" in app

design=source_root/"views/DesignSystem.swift"
s=design.read_text()
s=s.replace('static let gold = Color(red: 0.96, green: 0.76, blue: 0.08)', 'static let gold = Color(red: 0.02, green: 0.64, blue: 1.00)')
s=s.replace('static let purple = Color(red: 0.66, green: 0.18, blue: 1.00)', 'static let purple = Color(red: 0.10, green: 0.96, blue: 0.68)')
s=s.replace('static let accent = purple','static let accent = gold')
s=s.replace('Color(red: 0.035, green: 0.025, blue: 0.065)','Color(red: 0.018, green: 0.036, blue: 0.072)')
s=s.replace('Color(red: 0.070, green: 0.050, blue: 0.105)','Color(red: 0.038, green: 0.075, blue: 0.113)')
s=s.replace('Color(red: 0.105, green: 0.075, blue: 0.155)','Color(red: 0.054, green: 0.101, blue: 0.149)')
s=s.replace('Text("RUIZEN")', 'Text("TEAMMOD")').replace('Text(" CLIENT")','Text("27")')
design.write_text(s)

# The original Xcode scheme is retained to preserve references to the
# original PBX target (3105); only the product and the resulting IPA change.
# The brand icon is replaced by the separate macOS art generator.

# Replace the legacy launcher with a TEAMMOD27-branded entry point.
launcher=source_root/"views/StockLauncherHomeView.swift"
launcher.write_text("""import SwiftUI

struct StockLauncherHomeView: View {
    let onEnter: () -> Void

    var body: some View {
        ZStack {
            HTVScreenBackground()
            ScrollView {
                VStack(spacing: 22) {
                    Spacer(minLength: 32)
                    Image("TeammodBanner")
                        .resizable()
                        .scaledToFit()
                        .frame(maxWidth: 640)
                        .accessibilityLabel("TEAMMOD27")
                    Text("TEAMMOD27")
                        .font(.system(size: 36, weight: .black, design: .rounded))
                        .foregroundStyle(AppTheme.brandGradient)
                    Text("DEVICE TOOLS · AIRLIFT / RSD")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text("ตรวจสอบการเชื่อมต่ออุปกรณ์และจัดการไฟล์ที่ได้รับอนุญาต")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                    Button(action: onEnter) {
                        Label("เข้าสู่ TEAMMOD27", systemImage: "arrow.right.circle.fill")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 15)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.white)
                    .background(AppTheme.brandGradient, in: RoundedRectangle(cornerRadius: 16))
                    Spacer(minLength: 24)
                }
                .padding(.horizontal, 24)
            }
        }
        .preferredColorScheme(.dark)
    }
}
""",encoding="utf8")

repo_view=source_root/"views/RepositoryHomeView.swift"
contents=repo_view.read_text()
if "Image(\"TeammodBanner\")" not in contents:
    contents=contents.replace("                        brandHeader\\n", "                        brandHeader\\n                        Image(\"TeammodBanner\").resizable().scaledToFit().frame(maxWidth: 610)\\n",1)
repo_view.write_text(contents)

print("TEAMMOD27 branding, version and shared key identity configured.")
print("Bundle ID preserved:",info["CFBundleIdentifier"])
