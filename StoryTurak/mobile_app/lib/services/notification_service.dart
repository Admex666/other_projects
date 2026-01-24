import 'dart:typed_data'; // Required for Int64List
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  Future<void> init() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    final DarwinInitializationSettings initializationSettingsDarwin =
        DarwinInitializationSettings();

    final LinuxInitializationSettings initializationSettingsLinux =
        LinuxInitializationSettings(defaultActionName: 'Open notification');

    // Windows settings
    // 'appUserModelId' is required from error logs.
    const WindowsInitializationSettings initializationSettingsWindows =
        WindowsInitializationSettings(
            appName: 'storyturak_mobile',
            appUserModelId: 'com.adam.storyturak_mobile',
            guid: '0D18D077-2222-4444-8888-A8A8A8A8A8A8'
        );

    final InitializationSettings initializationSettings =
        InitializationSettings(
            android: initializationSettingsAndroid,
            iOS: initializationSettingsDarwin,
            macOS: initializationSettingsDarwin,
            linux: initializationSettingsLinux,
            windows: initializationSettingsWindows);
    
    await flutterLocalNotificationsPlugin.initialize(initializationSettings);
    
    // Request permissions for Android 13+
    await flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();
  }

  Future<void> showZoneNotification(String zoneName) async {
    // Int64List cannot be const, so we use final
    final AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'keldor_zone_channel',
      'Keldor Zones',
      channelDescription: 'Notifications when entering game zones',
      importance: Importance.max,
      priority: Priority.high,
      ticker: 'ticker',
      vibrationPattern: Int64List.fromList([0, 500, 200, 500]), // Custom vibration
      enableVibration: true,
      playSound: true,
    );
    
    final NotificationDetails platformChannelSpecifics =
        NotificationDetails(android: androidPlatformChannelSpecifics);
        
    await flutterLocalNotificationsPlugin.show(
      0,
      'Zóna Észlelve!',
      'Beléptél ide: $zoneName',
      platformChannelSpecifics,
      payload: 'zone_entry',
    );
  }
}
