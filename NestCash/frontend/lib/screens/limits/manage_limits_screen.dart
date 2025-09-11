// lib/screens/limits/manage_limits_screen.dart

import 'package:flutter/material.dart';
import 'package:frontend/models/limit.dart';
import 'package:frontend/services/limit_service.dart';
import 'add_limit_screen.dart';
import 'edit_limit_screen.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:frontend/services/nestcash_analytics_service.dart';

class ManageLimitsScreen extends StatefulWidget {
  final String userId;

  const ManageLimitsScreen({Key? key, required this.userId}) : super(key: key);

  @override
  _ManageLimitsScreenState createState() => _ManageLimitsScreenState();
}

class _ManageLimitsScreenState extends State<ManageLimitsScreen> {
  final LimitService _limitService = LimitService();
  List<Limit> _limits = [];
  LimitStatus? _limitStatus;
  bool _isLoading = true;
  String _errorMessage = '';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = '';
    });

    try {
      final limits = await _limitService.getLimits();
      final status = await _limitService.getLimitStatus();

      setState(() {
        _limits = limits;
        _limitStatus = status;
        _isLoading = false;
      });
      await NestCashAnalyticsService.trackScreenView('limits_screen');
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _deleteLimit(String limitId, String limitName) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('manageLimits.deleteTitle'.tr()),
          content: Text('manageLimits.deleteContent'.tr(namedArgs: {'limitName': limitName})),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text('manageLimits.cancelButton'.tr()),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              style: TextButton.styleFrom(foregroundColor: Colors.red),
              child: Text('manageLimits.deleteButton'.tr()),
            ),
          ],
        );
      },
    );

    if (confirm == true) {
      try {
        await _limitService.deleteLimit(limitId);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('manageLimits.deleteSuccess'.tr(namedArgs: {'limitName': limitName})),
            backgroundColor: Colors.green,
          ),
        );
        _loadData(); // Újratöltés
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('manageLimits.deleteError'.tr(namedArgs: {'error': e.toString()})),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Widget _buildStatusCard() {
    if (_limitStatus == null) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'manageLimits.overviewTitle'.tr(),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _buildStatusItem(
                  'manageLimits.totalLimits'.tr(),
                  _limitStatus!.totalLimits.toString(),
                  Colors.blue,
                ),
              ),
              Expanded(
                child: _buildStatusItem(
                  'manageLimits.activeLimits'.tr(),
                  _limitStatus!.activeLimits.toString(),
                  Colors.green,
                ),
              ),
              Expanded(
                child: _buildStatusItem(
                  'manageLimits.exceededLimits'.tr(),
                  _limitStatus!.exceededLimits.toString(),
                  Colors.red,
                ),
              ),
              Expanded(
                child: _buildStatusItem(
                  'manageLimits.warningLimits'.tr(),
                  _limitStatus!.warningLimits.toString(),
                  Colors.orange,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatusItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildLimitCard(Limit limit) {
    final usagePercentage = limit.usagePercentage ?? 0;
    final isExceeded = limit.isExceeded;
    final isNearLimit = limit.isNearLimit;

    Color progressColor = Colors.green;
    if (isExceeded) {
      progressColor = Colors.red;
    } else if (isNearLimit) {
      progressColor = Colors.orange;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => EditLimitScreen(
                userId: widget.userId,
                limit: limit,
              ),
            ),
          ).then((_) => _loadData());
        },
        borderRadius: BorderRadius.circular(15),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(
                      Icons.speed,
                      color: Colors.orange,
                      size: 24,
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          limit.name,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          limit.typeDisplayName,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'edit') {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => EditLimitScreen(
                              userId: widget.userId,
                              limit: limit,
                            ),
                          ),
                        ).then((_) => _loadData());
                      } else if (value == 'delete') {
                        _deleteLimit(limit.id, limit.name);
                      }
                    },
                    icon: Icon(Icons.more_vert, color: Colors.grey[600]),
                    itemBuilder: (BuildContext context) => [
                      PopupMenuItem(
                        value: 'edit',
                        child: Row(
                          children: [
                            Icon(Icons.edit, size: 20),
                            SizedBox(width: 8),
                            Text('Szerkesztés'.tr()),
                          ],
                        ),
                      ),
                      PopupMenuItem(
                        value: 'delete',
                        child: Row(
                          children: [
                            Icon(Icons.delete, size: 20, color: Colors.red),
                            SizedBox(width: 8),
                            Text('Törlés'.tr(), style: TextStyle(color: Colors.red)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${limit.currentSpending?.toStringAsFixed(0) ?? '0'} ${limit.currency}',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  ),
                  Text(
                    '/ ${limit.amount.toStringAsFixed(0)} ${limit.currency}',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                limit.period.displayName,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: usagePercentage / 100,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(progressColor),
                minHeight: 6,
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'manageLimits.used'.tr(namedArgs: {'usagePercentage': usagePercentage.toStringAsFixed(1)}),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: progressColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      limit.statusText,
                      style: TextStyle(
                        fontSize: 12,
                        color: progressColor,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
              if (limit.remainingAmount != null && limit.remainingAmount! > 0) ...[
                const SizedBox(height: 8),
                Text(
                  'manageLimits.remaining'.tr(namedArgs: {'remainingAmount': limit.remainingAmount!.toStringAsFixed(0), 'currency': limit.currency}),
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.green[700],
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFF00D4AA),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: Icon(
                      Icons.arrow_back,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                  Expanded(
                    child: Text(
                      'manageLimits.screenTitle'.tr(),
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  IconButton(
                    onPressed: _loadData,
                    icon: Icon(
                      Icons.refresh,
                      color: Colors.black87,
                      size: 24,
                    ),
                  ),
                ],
              ),
            ),

            // Content Container
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Color(0xFFF5F5F5),
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(30),
                    topRight: Radius.circular(30),
                  ),
                ),
                child: _isLoading
                    ? Center(
                        child: CircularProgressIndicator(
                          color: Color(0xFF00D4AA),
                        ),
                      )
                    : _errorMessage.isNotEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.error_outline,
                                    size: 64,
                                    color: Colors.grey[400],
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    'manageLimits.errorTitle'.tr(),
                                    style: TextStyle(
                                      fontSize: 18,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    _errorMessage,
                                    textAlign: TextAlign.center,
                                    style: TextStyle(
                                      color: Colors.grey[500],
                                    ),
                                  ),
                                  const SizedBox(height: 24),
                                  Container(
                                    width: double.infinity,
                                    height: 48,
                                    child: ElevatedButton(
                                      onPressed: _loadData,
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Color(0xFF00D4AA),
                                        foregroundColor: Colors.white,
                                        elevation: 0,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                      ),
                                      child: Text(
                                        'manageLimits.tryAgainButton'.tr(),
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          )
                        : SingleChildScrollView(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                children: [
                                  SizedBox(height: 10),

                                  // Gombok
                                  Container(
                                    width: double.infinity,
                                    height: 48,
                                    child: ElevatedButton.icon(
                                      onPressed: _loadData,
                                      icon: Icon(Icons.refresh, color: Colors.white),
                                      label: Text(
                                        'manageLimits.refreshButton'.tr(),
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.white,
                                        ),
                                      ),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Color(0xFF00D4AA),
                                        elevation: 0,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                      ),
                                    ),
                                  ),

                                  SizedBox(height: 12),

                                  Container(
                                    width: double.infinity,
                                    height: 48,
                                    child: ElevatedButton.icon(
                                      onPressed: () {
                                        Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                            builder: (context) => AddLimitScreen(userId: widget.userId),
                                          ),
                                        ).then((_) => _loadData());
                                      },
                                      icon: Icon(Icons.add, color: Colors.white),
                                      label: Text(
                                        'manageLimits.addButton'.tr(),
                                        style: TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.white,
                                        ),
                                      ),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.orange,
                                        elevation: 0,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                      ),
                                    ),
                                  ),

                                  SizedBox(height: 24),

                                  _buildStatusCard(),

                                  if (_limits.isEmpty)
                                    Container(
                                      padding: const EdgeInsets.all(40),
                                      child: Column(
                                        children: [
                                          Icon(
                                            Icons.speed,
                                            size: 64,
                                            color: Colors.grey[400],
                                          ),
                                          const SizedBox(height: 16),
                                          Text(
                                            'manageLimits.noLimitsTitle'.tr(),
                                            style: TextStyle(
                                              fontSize: 18,
                                              fontWeight: FontWeight.w600,
                                              color: Colors.grey[600],
                                            ),
                                          ),
                                          const SizedBox(height: 8),
                                          Text(
                                            'manageLimits.noLimitsContent'.tr(),
                                            style: TextStyle(
                                              color: Colors.grey[500],
                                            ),
                                            textAlign: TextAlign.center,
                                          ),
                                        ],
                                      ),
                                    )
                                  else
                                    ...(_limits.map((limit) => _buildLimitCard(limit)).toList()),

                                  SizedBox(height: 100), // Extra space for FAB
                                ],
                              ),
                            ),
                          ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => AddLimitScreen(userId: widget.userId),
            ),
          ).then((_) => _loadData());
        },
        backgroundColor: Colors.orange,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}