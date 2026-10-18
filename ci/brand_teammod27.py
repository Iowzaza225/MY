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


# Repair a pre-existing C syntax typo in the supplied source archive.
display=source_root/"helpers/DisplayIdentity.m"
txt=display.read_text()
marker="static const uint8_t kAttributionSeed[] = {"
if marker in txt:
    start=txt.index(marker)
    end=txt.find("\n}",start)
    if end>=0 and not txt[end+2:end+3]==";":
        txt=txt[:end]+"\n};"+txt[end+2:]
        display.write_text(txt)


# iOS 27 RemotePairing transport correction:
# 62078 is the lockdown port, not a guaranteed RSD/RemotePairing endpoint.
# Let the user set the advertised RSD port, defaulting to the commonly observed
# 49152, and retry raw RPPairing if a RemoteXPC handshake is rejected.
readiness = source_root / "helpers/RuizenDeviceReadiness.swift"
rtext = readiness.read_text()
old_host = '    @Published var targetHost = "10.7.0.1"'
assert rtext.count(old_host) == 1, "Readiness host declaration changed"
rtext = rtext.replace(old_host, old_host + '\n    @Published var targetPort = "49152"', 1)
old_port = '        let path = Self.pairingURL.path\n        isChecking = true'
assert rtext.count(old_port) == 1, "Probe input setup changed"
rtext = rtext.replace(old_port, '        let path = Self.pairingURL.path\n        let port = Int(targetPort.trimmingCharacters(in: .whitespacesAndNewlines)) ?? 0\n        isChecking = true', 1)
old_probe = 'RuizenNativeBridge.probePairing(atPath: path, host: host, port: 62078)'
assert rtext.count(old_probe) == 1, "Original fixed lockdown port not found"
rtext = rtext.replace(old_probe, 'RuizenNativeBridge.probePairing(atPath: path, host: host, port: port)', 1)
readiness.write_text(rtext)

preflight = source_root / "views/RuizenApplyPreflightView.swift"
ptext = preflight.read_text()
host_change = '''                                .onChange(of: readiness.targetHost) { _ in
                                    readiness.invalidate(reason: "เปลี่ยนปลายทางแล้ว ต้องตรวจ Pairing / Tunnel / RSD ใหม่")
                                }
'''
assert ptext.count(host_change) == 1, "RSD host input block changed"
new_port_field = '''                            TextField("Remote Pairing / RSD Port (เช่น 49152)", text: $readiness.targetPort)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.numberPad)
                                .textFieldStyle(.roundedBorder)
                                .onChange(of: readiness.targetPort) { _ in
                                    readiness.invalidate(reason: "เปลี่ยนพอร์ตแล้ว ต้องตรวจ Tunnel อีกครั้ง")
                                }
                            Text("พอร์ต 62078 เป็น Lockdown ไม่ใช่พอร์ต RSD เสมอไป • ค่า 49152 เป็นค่าเริ่มต้นสำหรับทดสอบ")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
'''
ptext = ptext.replace(host_change,host_change+new_port_field,1)
old_label = 'Text("RSD endpoint: \\(readiness.targetHost):62078")'
assert ptext.count(old_label) == 1, "Old endpoint label changed"
ptext = ptext.replace(old_label,'Text("Remote Pairing/RSD: \\(readiness.targetHost):\\(readiness.targetPort)")',1)
preflight.write_text(ptext)

bridge=source_root/"native/RuizenNativeBridge.m"
btext=bridge.read_text()
needle = '    RZCreateTunnel createTunnel = (RZCreateTunnel)dlsym(RTLD_DEFAULT, "tunnel_create_remotexpc_multihost");'
assert btext.count(needle)==1, "RemoteXPC native function changed"
btext=btext.replace(needle, needle + '\n    RZCreateTunnel createRaw = (RZCreateTunnel)dlsym(RTLD_DEFAULT, "tunnel_create_rppairing_multihost");',1)

original='''    void *adapter = NULL;
    void *handshake = NULL;
    error = createTunnel((const struct sockaddr *)&address, sizeof(address),
                         "TEAMMOD27", pairing, NULL, NULL, NULL, 0,
                         &failureKind, &adapter, &handshake);
    freePairing(pairing);
    if (error || !adapter || !handshake) {
        NSString *ffiDetail = RZMessage(error, freeError);
        detail = [NSString stringWithFormat:@"%@: %@", RZFailureExplanation(failureKind), ffiDetail];
        if (handshake) freeHandshake(handshake);
        if (adapter) freeAdapter(adapter);
        goto finish;
    }
    tunnel = YES; // Tunnel constructor performed pair-verify and RSD handshake.
'''
assert btext.count(original)==1, "Native Tunnel invocation changed"
replacement='''    void *adapter = NULL;
    void *handshake = NULL;
    error = createTunnel((const struct sockaddr *)&address, sizeof(address),
                         "TEAMMOD27", pairing, NULL, NULL, NULL, 0,
                         &failureKind, &adapter, &handshake);
    NSString *remoteError = @"";
    if (error || !adapter || !handshake) {
        remoteError = [NSString stringWithFormat:@"%@: %@",
                       RZFailureExplanation(failureKind), RZMessage(error, freeError)];
        if (handshake) freeHandshake(handshake);
        if (adapter) freeAdapter(adapter);
        handshake = NULL;
        adapter = NULL;
        if (createRaw) {
            failureKind = 0;
            error = createRaw((const struct sockaddr *)&address, sizeof(address),
                              "TEAMMOD27", pairing, NULL, NULL, NULL, 0,
                              &failureKind, &adapter, &handshake);
            if (error || !adapter || !handshake) {
                NSString *rawError = [NSString stringWithFormat:@"%@: %@",
                                       RZFailureExplanation(failureKind),
                                       RZMessage(error, freeError)];
                detail = [NSString stringWithFormat:@"RemoteXPC: %@ | Raw RPPairing: %@",
                          remoteError, rawError];
                if (handshake) freeHandshake(handshake);
                if (adapter) freeAdapter(adapter);
                freePairing(pairing);
                goto finish;
            }
        } else {
            detail = [NSString stringWithFormat:@"RemoteXPC: %@ | Raw RPPairing ไม่พร้อม", remoteError];
            freePairing(pairing);
            goto finish;
        }
    }
    freePairing(pairing);
    tunnel = YES; // Successful native tunnel and authenticated RSD handshake.
'''
btext=btext.replace(original,replacement,1)
# Objective-C ARC does not permit goto to jump over a __strong local initializer.
# Keep the diagnostic variable at the beginning of the method's lifetime.
assert btext.count('    NSString *detail = @"";') == 1
btext=btext.replace('    NSString *detail = @"";',
                    '    NSString *detail = @"";' + chr(10) + '    NSString *remoteError = @"";',1)
assert btext.count('    NSString *remoteError = @"";') == 2
btext=btext.replace('    NSString *remoteError = @"";' + chr(10) + '    if (error || !adapter || !handshake)',
                    '    remoteError = @"";' + chr(10) + '    if (error || !adapter || !handshake)',1)
bridge.write_text(btext)

# Remove one stale old-brand instructional message without changing FFI.
preflight_text=preflight.read_text().replace("ให้กลับเข้า RUIZEN", "ให้กลับเข้า TEAMMOD27")
preflight.write_text(preflight_text)
print("TEAMMOD27 iOS 27 RSD port correction and Raw RPPairing fallback staged.")

print("TEAMMOD27 branding, version and shared key identity configured.")
print("Bundle ID preserved:",info["CFBundleIdentifier"])
