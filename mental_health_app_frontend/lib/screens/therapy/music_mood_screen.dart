import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../services/api_service.dart';
import 'music_player_screen.dart';
import '../../theme/app_theme.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/gradient_button.dart';

class MusicMoodScreen extends StatefulWidget {
  const MusicMoodScreen({super.key});

  @override
  State<MusicMoodScreen> createState() => _MusicMoodScreenState();
}

class _MusicMoodScreenState extends State<MusicMoodScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _sessions = [];
  bool _isLoading = true;
  String? _selectedMood;
  int? _selectedSessionId;

  final List<String> _moods = [
    'Happy', 'Calm', 'Sad', 'Angry', 'Tired', 'Anxious', 'Stressed', 'Grateful', 'Loved', 'Excited'
  ];

  @override
  void initState() {
    super.initState();
    _fetchSessions();
  }

  Future<void> _fetchSessions() async {
    try {
      final sessions = await _apiService.getTherapySessions('Music');
      setState(() {
        _sessions = sessions;
        _isLoading = false;
        if (_sessions.length == 1) {
          _selectedSessionId = _sessions[0]['id'];
        }
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  void _startSession() {
    if (_selectedMood == null || _selectedSessionId == null) return;
    
    final session = _sessions.firstWhere((s) => s['id'] == _selectedSessionId);

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => MusicPlayerScreen(
          session: session,
          moodBefore: _selectedMood!,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    bool canStart = _selectedMood != null && _selectedSessionId != null;
    
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text('Music Therapy', style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: AppTheme.textDark)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: AppTheme.textDark),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SafeArea(
        child: _isLoading
            ? const Center(child: CircularProgressIndicator(color: AppTheme.primaryColor))
            : SingleChildScrollView(
                physics: const BouncingScrollPhysics(),
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "How are you feeling?",
                      style: GoogleFonts.outfit(
                        fontSize: 26,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textDark
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "Select your current state of mind to get started.",
                      style: GoogleFonts.outfit(fontSize: 16, color: AppTheme.textLight),
                    ),
                    const SizedBox(height: 24),
                    
                    // Mood Grid
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        mainAxisSpacing: 16,
                        crossAxisSpacing: 16,
                        childAspectRatio: 1.0,
                      ),
                      itemCount: _moods.length,
                      itemBuilder: (context, index) {
                        final mood = _moods[index];
                        final isSelected = _selectedMood == mood;
                        return GestureDetector(
                          onTap: () => setState(() => _selectedMood = isSelected ? null : mood),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            decoration: BoxDecoration(
                              color: isSelected ? AppTheme.primaryColor : Colors.white,
                              borderRadius: BorderRadius.circular(20),
                              boxShadow: [
                                BoxShadow(
                                  color: isSelected 
                                      ? AppTheme.primaryColor.withOpacity(0.4) 
                                      : Colors.black.withOpacity(0.05),
                                  blurRadius: 10,
                                  offset: const Offset(0, 4),
                                )
                              ],
                              border: Border.all(
                                color: isSelected ? AppTheme.primaryColor : Colors.transparent,
                                width: 2,
                              ),
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                 Text(
                                   _getMoodEmoji(mood),
                                   style: const TextStyle(fontSize: 32),
                                 ),
                                const SizedBox(height: 8),
                                Text(
                                  mood,
                                  style: GoogleFonts.outfit(
                                    fontSize: 13,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.w600,
                                    color: isSelected ? Colors.white : AppTheme.textDark,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),

                    const SizedBox(height: 32),
                    
                    if (_sessions.isNotEmpty) ...[
                      Text(
                        "Recommended Sessions",
                        style: GoogleFonts.outfit(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.textDark
                        ),
                      ),
                      const SizedBox(height: 16),
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _sessions.length,
                        itemBuilder: (context, index) {
                          final session = _sessions[index];
                          final isSelected = _selectedSessionId == session['id'];
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12.0),
                            child: GlassCard(
                              onTap: () => setState(() => _selectedSessionId = session['id']),
                              padding: const EdgeInsets.all(16),
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: isSelected ? AppTheme.primaryColor : AppTheme.primaryColor.withOpacity(0.1),
                                      shape: BoxShape.circle,
                                    ),
                                     child: Icon(
                                       Icons.music_note_rounded,
                                       color: isSelected ? Colors.white : AppTheme.primaryColor,
                                       size: 20,
                                     ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          session['title'],
                                          style: GoogleFonts.outfit(
                                            fontSize: 17,
                                            fontWeight: FontWeight.bold,
                                            color: AppTheme.textDark,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          "Audio Session",
                                          style: GoogleFonts.outfit(
                                            fontSize: 13,
                                            color: AppTheme.textLight,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (isSelected)
                                    const Icon(Icons.check_circle_rounded, color: AppTheme.primaryColor),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ] else
                      Center(
                        child: Text(
                          "No sessions available at the moment.",
                          style: GoogleFonts.outfit(color: AppTheme.textLight),
                        ),
                      ),
                    
                    const SizedBox(height: 32),
                    GradientButton(
                      text: "Start Session",
                      onPressed: canStart ? _startSession : null,
                       icon: Icons.play_circle_outline_rounded,
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
      ),
    );
  }

  String _getMoodEmoji(String mood) {
    switch (mood) {
      case 'Anxious': return '😰';
      case 'Sad': return '😔';
      case 'Angry': return '😠';
      case 'Tired': return '😴';
      case 'Stressed': return '😫';
      case 'Calm': return '😌';
      case 'Grateful': return '✨';
      case 'Loved': return '🥰';
      case 'Excited': return '🤩';
      case 'Happy': return '😊';
      default: return '😊';
    }
  }
}
