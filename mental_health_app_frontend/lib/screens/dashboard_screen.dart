import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/glass_card.dart';
import '../widgets/gradient_button.dart';
import '../widgets/feature_info_sheet.dart';
import '../data/feature_content.dart';

// Screens
import 'calming_screen.dart';
import 'meditation_yoga_screen.dart';
import 'mood_tracker.dart';
import 'sos_button.dart';
import 'sos_confirmation.dart';
import 'stress_buster_screen.dart';
import 'profile.dart';
import 'affirmations_home.dart';
import 'cbt_therapy/cbt_topics_screen.dart';
import 'resources_hub/disorder_selection.dart';
import 'tri_modal_journal_screen.dart';
import 'maa_chat_screen.dart';
import 'therapy/therapy_home_screen.dart';
import 'therapy/art_therapy_home.dart';

class DashboardScreen extends StatefulWidget {
  DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  
  // Greeting based on time of day
  String get _greeting {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  Map<String, dynamic>? _lastMood;
  bool _isMoodLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchMoodData();
  }

  Future<void> _fetchMoodData() async {
    try {
      final logs = await _apiService.getMoodLogs(period: 'week');
      if (logs.isNotEmpty) {
        setState(() {
          _lastMood = logs[0];
          _isMoodLoading = false;
        });
      } else {
        setState(() => _isMoodLoading = false);
      }
    } catch (e) {
      print('Error fetching dashboard mood: $e');
      setState(() => _isMoodLoading = false);
    }
  }

  void _openTriModalJournal() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => TriModalJournalScreen(cameras: []), 
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: Stack(
        children: [
          // 🌸 Background Decoration (Abstract Shapes)
          Positioned(
            top: -50,
            left: -50,
            child: Opacity(
              opacity: 0.5,
              child: Image.asset(
                'assets/images/abstract_shapes.png', 
                width: 300,
                color: AppTheme.mintGreen.withOpacity(0.3),
                colorBlendMode: BlendMode.srcIn,
              ),
            ),
          ),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 120), // Extra bottom padding for floating nav
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1️⃣ Header
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _greeting,
                            style: GoogleFonts.outfit( // Using Outfit/Nunito as planned
                              fontSize: 18,
                              color: AppTheme.textLight,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            'How are you feeling?',
                            style: GoogleFonts.outfit(
                              fontSize: 26,
                              color: AppTheme.textDark,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      GestureDetector(
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const ProfileScreen()),
                        ),
                        child: Container(
                          padding: const EdgeInsets.all(2),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(color: AppTheme.primaryColor.withOpacity(0.2), width: 2),
                          ),
                          child: CircleAvatar(
                            radius: 22,
                            backgroundColor: AppTheme.softPurple,
                            backgroundImage: const AssetImage('assets/images/zen_avatar.png'),
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 24),

                  // 2️⃣ Mood Selector Row
                  _buildMoodSelector(),

                  const SizedBox(height: 32),

                  // 3️⃣ Hero Card: "Talk to MAA"
                  GestureDetector(
                    onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const MAAChatScreen()),
                    ),
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryColor,
                        borderRadius: BorderRadius.circular(32),
                        boxShadow: [
                          BoxShadow(
                            color: AppTheme.primaryColor.withOpacity(0.3),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.1),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    'AI Companion',
                                    style: GoogleFonts.outfit(
                                      color: AppTheme.accentColor,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  'Talk to MAA',
                                  style: GoogleFonts.outfit(
                                    fontSize: 22,
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  "I'm here to listen. Tell me what's on your mind.",
                                  style: GoogleFonts.outfit(
                                    fontSize: 14,
                                    color: Colors.white.withOpacity(0.8),
                                    height: 1.4,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Image.asset('assets/images/bot_avatar.png', height: 100),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // 4️⃣ "What do you want to work on?" Title
                  Text(
                    'What do you want to work on?',
                    style: GoogleFonts.outfit(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textDark,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 5️⃣ Unified Feature Grid
                  GridView.count(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: 2,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: 0.85,
                    children: [
                      // Meditation
                      _buildMellowCard(
                        context,
                        title: 'Meditation',
                        imagePath: 'assets/images/meditation_hero.png',
                        bgColor: AppTheme.mintGreen,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const MeditationYogaScreen()),
                        ),
                      ),
                      // Journal
                      _buildMellowCard(
                        context,
                        title: 'Journal',
                        imagePath: 'assets/images/icon_writing.png',
                        bgColor: AppTheme.softPink,
                        onTap: _openTriModalJournal,
                      ),
                      // Therapy Room
                      _buildMellowCard(
                        context,
                        title: 'Therapy Room',
                        imagePath: 'assets/images/icon_paint.png', // Using palette for general therapy
                        bgColor: AppTheme.mellowYellow,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const TherapyHomeScreen()),
                        ),
                      ),
                      // Stress Buster
                      _buildMellowCard(
                        context,
                        title: 'Stress Buster',
                        imagePath: 'assets/images/abstract_shapes.png', // Using abstract as placeholder or fallback
                        bgColor: const Color(0xFFD4E4F7), // Soft Blue
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const StressBusterScreen()),
                        ),
                        isAbstract: true,
                      ),
                      // Resources
                      _buildMellowCard(
                        context,
                        title: 'Resources',
                        imagePath: 'assets/images/contemplation.png',
                        bgColor: AppTheme.softPurple,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const DisorderSelectionScreen()),
                        ),
                      ),
                      // Affirmations
                      _buildMellowCard(
                        context,
                        title: 'Affirmations',
                        imagePath: 'assets/images/affirmation_bg.png', // Using bg as card art
                        bgColor: const Color(0xFFFFE0B2), // Soft Orange
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => AffirmationsHomeScreen()),
                        ),
                        isAbstract: true,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // ⚓ Floating Bottom Nav Bar
          Positioned(
            bottom: 32,
            left: 24,
            right: 24,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor,
                borderRadius: BorderRadius.circular(32),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primaryColor.withOpacity(0.4),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(Icons.home_rounded, true, () {}),
                  _buildNavItem(Icons.chat_bubble_rounded, false, () {
                     Navigator.push(context, MaterialPageRoute(builder: (context) => const MAAChatScreen()));
                  }),
                  _buildNavItem(Icons.person_rounded, false, () {
                    Navigator.push(context, MaterialPageRoute(builder: (context) => const ProfileScreen()));
                  }),
                  // SOS Red Button inside Nav
                  GestureDetector(
                    onTap: () {
                       // Trigger SOS logic directly or show modal
                       // For safety, let's just push the SOS button widget or dialog
                       showModalBottomSheet(
                         context: context, 
                         backgroundColor: Colors.transparent,
                         builder: (context) => Container(
                           padding: const EdgeInsets.all(24),
                           decoration: const BoxDecoration(
                             color: Colors.white,
                             borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
                           ),
                           child: Column(
                             mainAxisSize: MainAxisSize.min,
                             children: [
                               const Text("Emergency?", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                               const SizedBox(height: 20),
                               SOSButtonWidget(onTriggered: (name) {
                                  Navigator.pop(context);
                                  Navigator.push(context, MaterialPageRoute(builder: (context) => SOSConfirmationScreen(guardianName: name)));
                               }),
                             ],
                           ),
                         )
                       );
                    },
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppTheme.errorColor,
                        shape: BoxShape.circle,
                        boxShadow: [BoxShadow(color: AppTheme.errorColor.withOpacity(0.4), blurRadius: 10)],
                      ),
                      child: const Icon(Icons.sos_rounded, color: Colors.white, size: 24),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMoodSelector() {
    final moods = [
      {'val': 'happy', 'img': 'assets/images/mood_joy.png', 'label': 'Happy'},
      {'val': 'sad', 'img': 'assets/images/mood_sad.png', 'label': 'Sad'},
      {'val': 'calm', 'img': 'assets/images/mood_calm.png', 'label': 'Calm'},
      {'val': 'angry', 'img': 'assets/images/mood_angry.png', 'label': 'Angry'},
      {'val': 'tired', 'img': 'assets/images/mood_tired.png', 'label': 'Tired'},
    ];

    return SizedBox(
      height: 90,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: moods.length,
        separatorBuilder: (_, __) => const SizedBox(width: 16),
        itemBuilder: (context, index) {
          final m = moods[index];
          return GestureDetector(
            onTap: () async {
              // Navigate to mood tracker
              await Navigator.push(
                context, 
                MaterialPageRoute(builder: (context) => const MoodTrackerScreen())
              );
              _fetchMoodData();
            },
            child: Column(
              children: [
                Container(
                  height: 60,
                  width: 60,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    image: DecorationImage(image: AssetImage(m['img']!), fit: BoxFit.cover),
                    boxShadow: [
                       BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4)),
                    ]
                  ),
                ),
                const SizedBox(height: 8),
                Text(m['label']!, style: GoogleFonts.outfit(fontSize: 12, fontWeight: FontWeight.w500)),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildMellowCard(BuildContext context, {
    required String title,
    required String imagePath,
    required Color bgColor,
    required VoidCallback onTap,
    bool isAbstract = false,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(32),
        ),
        child: Stack(
          children: [
            // Image
            Positioned(
              right: -10,
              bottom: -10,
              child: Image.asset(
                imagePath,
                width: isAbstract ? 120 : 100, // Larger for abstract backgrounds
                height: isAbstract ? 120 : 100,
                opacity: isAbstract ? const AlwaysStoppedAnimation(0.6) : null,
              ),
            ),
            // Text
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text(
                title,
                style: GoogleFonts.outfit(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.textDark,
                ),
              ),
            ),
            // Arrow Icon
            Positioned(
              top: 20,
              right: 20,
              child: Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.5),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.arrow_outward_rounded, size: 16, color: AppTheme.textDark),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildNavItem(IconData icon, bool isActive, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: isActive ? BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          borderRadius: BorderRadius.circular(16),
        ) : null,
        child: Icon(icon, color: isActive ? AppTheme.accentColor : Colors.white.withOpacity(0.6), size: 28),
      ),
    );
  }}
