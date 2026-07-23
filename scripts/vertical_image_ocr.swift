import AppKit
import Foundation
import Vision

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write(Data("usage: vertical_image_ocr.swift <image>\n".utf8))
    exit(2)
}

let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
guard
    let image = NSImage(contentsOf: imageURL),
    let data = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: data),
    let cgImage = bitmap.cgImage
else {
    FileHandle.standardError.write(Data("cannot read image\n".utf8))
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
request.usesLanguageCorrection = true
let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try handler.perform([request])

let observations = (request.results ?? []).compactMap { observation -> [String: Any]? in
    guard let candidate = observation.topCandidates(1).first else { return nil }
    let box = observation.boundingBox
    return [
        "text": candidate.string,
        "confidence": candidate.confidence,
        "x": box.origin.x,
        "y": box.origin.y,
        "width": box.size.width,
        "height": box.size.height,
    ]
}

let output = try JSONSerialization.data(
    withJSONObject: observations,
    options: [.sortedKeys]
)
FileHandle.standardOutput.write(output)
