import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/api_service.dart';
import 'mood_journal.dart';
import '../theme/app_theme.dart';
import '../widgets/glass_card.dart';
import '../widgets/gradient_button.dart';
import '../widgets/custom_text_field.dart';

class MoodTrackerScreen extends StatefulWidget {
  const MoodTrackerScreen({super.key});

  @override
  _MoodTrackerScreenState createState() => _MoodTrackerScreenState();
}

class _MoodTrackerScreenState extends State<MoodTrackerScreen> {
  final _apiService = ApiService();
  String? _selectedMoodVal;
  String? _selectedMoodLabel;
  final _noteController = TextEditingController();
  String? _selectedTag;
  bool _isLoading = false;

  final List<Map<String, dynamic>> _moods = [
    {'val': 'happy', 'icon': '😊', 'label': 'Happy', 'color': Colors.amber},
    {'val': 'calm', 'icon': '😌', 'label': 'Calm', 'color': Colors.teal},
    {'val': 'sad', 'icon': '😔', 'label': 'Sad', 'color': Colors.blue},
    {'val': 'angry', 'icon': '😠', 'label': 'Angry', 'color': Colors.red},
    {'val': 'tired', 'icon': '😴', 'label': 'Tired', 'color': Colors.indigo},
    {'val': 'anxious', 'icon': '😰', 'label': 'Anxious', 'color': Colors.orange},
    {'val': 'stressed', 'icon': '😫', 'label': 'Stressed', 'color': Colors.deepOrange},
    {'val': 'grateful', 'icon': '✨', 'label': 'Grateful', 'color': Colors.purple},
    {'val': 'loved', 'icon': '🥰', 'label': 'Loved', 'color': Colors.pink},
    {'val': 'excited', 'icon': '🤩', 'label': 'Excited', 'color': Colors.yellow},
  ];

  Future<void> _saveMood() async {
    if (_selectedMoodVal == null) return;

    setState(() => _isLoading = true);
    
    try {
      await _apiService.logMood(
        moodEmoji: _selectedMoodVal!, 
        moodLabel: _selectedMoodLabel!,
        note: _noteController.text.isNotEmpty ? _noteController.text : null,
        tag: _selectedTag,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mood logged successfully')),
        );
        _noteController.clear();
        setState(() {
          _selectedMoodVal = null;
          _selectedMoodLabel = null;
          _selectedTag = null;
          _isLoading = false;
        });
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to log mood: $e'), backgroundColor: AppTheme.errorColor),
        );
      }
    }
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  Color _getBackgroundColor() {
    if (_selectedMoodVal == null) return AppTheme.backgroundColor;
    final mood = _moods.firstWhere((m) => m['val'] == _selectedMoodVal, orElse: () => _moods[0]);
    return (mood['color'] as Color).withOpacity(0.08);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 500),
      curve: Curves.easeInOut,
      color: _getBackgroundColor(),
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(
            'Check In',
            style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: AppTheme.textDark),
          ),
          backgroundColor: Colors.transparent,
          elevation: 0,
          centerTitle: true,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_rounded, color: AppTheme.textDark),
            onPressed: () => Navigator.pop(context),
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.history_rounded, color: AppTheme.primaryColor),
              onPressed: () {
                 Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const MoodJournalScreen()),
                );
              },
            )
          ],
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 10),
                
                Text(
                  'How are you feeling?',
                  style: GoogleFonts.outfit(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textDark,
                  ),
                  textAlign: TextAlign.center,
                ).animate().fadeIn().slideY(begin: 0.3, end: 0),
                
                const SizedBox(height: 8),
                
                Text(
                  'Select the mood that fits you best right now',
                  style: GoogleFonts.outfit(
                    fontSize: 16,
                    color: AppTheme.textLight,
                  ),
                  textAlign: TextAlign.center,
                ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.3, end: 0),

                const SizedBox(height: 40),

                // Hero Emoji Preview
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 400),
                  transitionBuilder: (child, animation) {
                    return ScaleTransition(scale: animation, child: FadeTransition(opacity: animation, child: child));
                  },
                  child: _selectedMoodVal != null
                      ? Column(
                          key: ValueKey(_selectedMoodVal),
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(24),
                              decoration: BoxDecoration(
                                color: (_moods.firstWhere((m) => m['val'] == _selectedMoodVal)['color'] as Color).withOpacity(0.15),
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: (_moods.firstWhere((m) => m['val'] == _selectedMoodVal)['color'] as Color).withOpacity(0.3),
                                  width: 2,
                                ),
                              ),
                              child: Text(
                                _moods.firstWhere((m) => m['val'] == _selectedMoodVal)['icon'],
                                style: const TextStyle(fontSize: 80),
                              ),
                            ),
                            const SizedBox(height: 20),
                            Text(
                              _selectedMoodLabel!,
                              style: GoogleFonts.outfit(
                                fontSize: 26,
                                fontWeight: FontWeight.bold,
                                color: _moods.firstWhere((m) => m['val'] == _selectedMoodVal)['color'],
                              ),
                            ),
                          ],
                        )
                      : SizedBox(height: 180, key: const ValueKey('empty'), 
                          child: Center(
                             child: Text('💓', style: TextStyle(fontSize: 60, color: AppTheme.primaryColor.withOpacity(0.2))),
                          ),
                        ),
                ),

                const SizedBox(height: 40),

                // Expanded Mood Grid
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 3,
                    mainAxisSpacing: 16,
                    crossAxisSpacing: 16,
                    childAspectRatio: 0.9,
                  ),
                  itemCount: _moods.length,
                  itemBuilder: (context, index) {
                     final mood = _moods[index];
                     final isSelected = _selectedMoodVal == mood['val'];
                     final moodColor = mood['color'] as Color;

                     return GestureDetector(
                       onTap: () {
                         setState(() {
                           _selectedMoodVal = mood['val'];
                           _selectedMoodLabel = mood['label'];
                         });
                       },
                       child: AnimatedContainer(
                         duration: const Duration(milliseconds: 250),
                         decoration: BoxDecoration(
                           color: isSelected ? Colors.white : Colors.white.withOpacity(0.5),
                           borderRadius: BorderRadius.circular(24),
                           border: Border.all(
                             color: isSelected ? moodColor : Colors.transparent,
                             width: 2,
                           ),
                           boxShadow: isSelected 
                             ? [BoxShadow(color: moodColor.withOpacity(0.2), blurRadius: 15, offset: const Offset(0, 8))]
                             : [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10)],
                         ),
                         child: Column(
                           mainAxisAlignment: MainAxisAlignment.center,
                           children: [
                             Text(
                               mood['icon'],
                               style: const TextStyle(fontSize: 40),
                             ),
                             const SizedBox(height: 10),
                             Text(
                               mood['label']!,
                               style: GoogleFonts.outfit(
                                 fontSize: 13,
                                 fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                 color: isSelected ? AppTheme.textDark : AppTheme.textLight,
                               ),
                             ),
                           ],
                         ),
                       ).animate().scale(begin: const Offset(0.9, 0.9), end: const Offset(1, 1), delay: (index * 30).ms),
                     );
                  },
                ),

                const SizedBox(height: 40),

                // Input Section
                AnimatedSize(
                  duration: const Duration(milliseconds: 400),
                  curve: Curves.fastOutSlowIn,
                  child: _selectedMoodVal == null
                      ? const SizedBox()
                      : Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Describe your day',
                              style: GoogleFonts.outfit(
                                fontSize: 18, 
                                fontWeight: FontWeight.w600, 
                                color: AppTheme.textDark
                              ),
                            ),
                            const SizedBox(height: 12),
                            CustomTextField(
                              controller: _noteController,
                              hintText: "Write a short note...",
                              maxLines: 3,
                               prefixIcon: Icons.edit_note_rounded,
                            ),
                            const SizedBox(height: 30),
                            
                            GradientButton(
                              text: "Save Mood",
                              onPressed: _saveMood,
                              isLoading: _isLoading,
                               icon: Icons.check_circle_outline_rounded,
                            ),
                          ],
                        ),
                ),
                
                const SizedBox(height: 60),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
