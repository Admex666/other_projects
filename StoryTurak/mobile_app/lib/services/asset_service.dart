
import 'package:flutter/material.dart';
import '../models/story.dart';

class AssetService {
  static Future<void> preloadStoryAssets(BuildContext context, Story story) async {
    for (var node in story.nodes.values) {
      if (node.image != null) {
        try {
          await precacheImage(AssetImage(node.image!), context);
        } catch (e) {
          print("Failed to preload asset: ${node.image}");
        }
      }
    }
  }
}
