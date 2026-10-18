import AppKit
import Foundation

let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let assetRoot = root.appendingPathComponent("ThreeOneOSFive/Assets.xcassets", isDirectory:true)
let blue = NSColor(calibratedRed:0.02,green:0.61,blue:0.99,alpha:1)
let teal = NSColor(calibratedRed:0.08,green:0.89,blue:0.79,alpha:1)
let green = NSColor(calibratedRed:0.08,green:0.97,blue:0.55,alpha:1)
let background = NSColor(calibratedRed:0.018,green:0.035,blue:0.072,alpha:1)

func render(_ width:Int,_ height:Int,_ path:URL, banner:Bool=false) throws {
    let w=CGFloat(width), h=CGFloat(height)
    let image=NSImage(size:NSSize(width:w,height:h))
    image.lockFocus()
    let bounds=NSRect(x:0,y:0,width:w,height:h)
    background.setFill()
    bounds.fill()
    let gradient=NSGradient(starting:blue,ending:green)!
    let inset:CGFloat = banner ? 12:32
    let box=NSBezierPath(roundedRect:bounds.insetBy(dx:inset,dy:inset),xRadius:banner ? 28:140,yRadius:banner ? 28:140)
    box.lineWidth=banner ? 7:14
    gradient.draw(in:box,angle:0)
    background.setFill()
    let inner=NSBezierPath(roundedRect:bounds.insetBy(dx:inset+13,dy:inset+13),xRadius:banner ? 22:125,yRadius:banner ? 22:125)
    inner.fill()
    // Accent haloes and a strong T/M monogram make the logo readable at icon size.
    teal.withAlphaComponent(0.18).setFill()
    NSBezierPath(ovalIn:NSRect(x:w*0.13,y:h*0.17,width:w*0.75,height:h*0.75)).fill()
    background.setFill()
    NSBezierPath(ovalIn:NSRect(x:w*0.18,y:h*0.22,width:w*0.64,height:h*0.64)).fill()
    let monoFont=NSFont.systemFont(ofSize:banner ? 210 : 430,weight:.black)
    let monoAttrs:[NSAttributedString.Key:Any]=[
        .font:monoFont,
        .foregroundColor:teal,
        .kern: banner ? -18 : -37
    ]
    let heading=NSAttributedString(string:"TM",attributes:monoAttrs)
    let size=heading.size()
    let x = banner ? w*0.065 : (w-size.width)/2
    let y = banner ? (h-size.height)/2+8 : h*0.22
    heading.draw(at:NSPoint(x:x,y:y))
    let label=NSAttributedString(string:"TEAMMOD27",attributes:[
        .font:NSFont.systemFont(ofSize:banner ? 154 : 100,weight:.heavy),
        .foregroundColor:NSColor.white,
        .kern:banner ? 1 : -2
    ])
    let dim=label.size()
    label.draw(at:NSPoint(x:banner ? w*0.43 : (w-dim.width)/2,y:banner ? (h-dim.height)/2 : h*0.14))
    image.unlockFocus()
    guard let tiff=image.tiffRepresentation, let bitmap=NSBitmapImageRep(data:tiff),
        let png=bitmap.representation(using:.png,properties:[:]) else {
        fatalError("Artwork PNG encoding failed")
    }
    try FileManager.default.createDirectory(at:path.deletingLastPathComponent(),withIntermediateDirectories:true)
    try png.write(to:path)
    print("Created \(path.path): \(png.count) bytes")
}
try render(1024,1024,assetRoot.appendingPathComponent("AppIcon.appiconset/AppIcon-1024.png"))
try render(600,600,assetRoot.appendingPathComponent("TeammodIcon.imageset/TeammodIcon.png"))
try render(1400,390,assetRoot.appendingPathComponent("TeammodBanner.imageset/TeammodBanner.png"),banner:true)
for (name, file) in [("TeammodIcon","TeammodIcon.png"),("TeammodBanner","TeammodBanner.png")] {
    let dir=assetRoot.appendingPathComponent("\(name).imageset")
    let json="{\"images\":[{\"filename\":\"\(file)\",\"idiom\":\"universal\"}],\"info\":{\"author\":\"xcode\",\"version\":1}}"
    try json.write(to:dir.appendingPathComponent("Contents.json"),atomically:true,encoding:.utf8)
}
