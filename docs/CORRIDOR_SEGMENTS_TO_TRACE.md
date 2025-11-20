# 🗺️ Building M - Corridor Segments to Trace

## 📋 Complete List: 28 Corridor Segments

Based on your navigation graph, here are ALL corridor segments (node-to-node connections) you need to trace:

---

## **PATH 1: Main Entrance Corridor** (7 segments)

1. ☐ **H_entry ↔ M1_1** - Building H connection to Building M
2. ☐ **M1_1 ↔ M1_2** - Entry corridor
3. ☐ **M1_2 ↔ M1_3** - Toward Room 1006
4. ☐ **M1_3 ↔ M1_Int_1** - To first intersection
5. ☐ **M1_Int_1 ↔ M1_4** - Toward Room 1004
6. ☐ **M1_4 ↔ M1_5** - Continuing corridor
7. ☐ **M1_5 ↔ M1_6** - To Room 1003
8. ☐ **M1_6 ↔ M1_7** - To main exit

---

## **PATH 2: Short Connector** (2 segments)

9. ☐ **M1_Int_1 ↔ M1_Turn_1** - T-intersection connector
10. ☐ **M1_Turn_1 ↔ M1_8** - Turn to next corridor

---

## **PATH 3: Bathroom Corridor** (7 segments)

11. ☐ **M1_8 ↔ M1_Int_2** - To second intersection
12. ☐ **M1_Int_2 ↔ M1_9** - To Men's Bathroom
13. ☐ **M1_9 ↔ M1_10** - Accessible Bathroom area
14. ☐ **M1_10 ↔ M1_11** - To Women's Bathroom
15. ☐ **M1_11 ↔ M1_12** - Continuing corridor
16. ☐ **M1_12 ↔ M1_Turn_2** - Approaching turn
17. ☐ **M1_Turn_2 ↔ M1_13** - To north exit

---

## **PATH 4: Side Branch Corridor** (7 segments)

18. ☐ **M1_Int_2 ↔ M1_14** - Branch from intersection
19. ☐ **M1_14 ↔ M1_15** - To Room 1035/1037 area
20. ☐ **M1_15 ↔ M1_16** - To Room 1030/1041 area
21. ☐ **M1_16 ↔ M1_Turn_3** - Approaching final turn
22. ☐ **M1_Turn_3 ↔ M1_17** - After turn
23. ☐ **M1_17 ↔ M1_18** - To Room 1049 area
24. ☐ **M1_18 ↔ M1_19** - To final exit

---

## 📊 **Summary**

- **Total Segments:** 24 corridor segments
- **Estimated Time:** 24 × 2 minutes = **~48 minutes** (less than 1 hour!)
- **Coverage:** ALL 210 possible room combinations ✅
- **Quality:** Smooth, professional paths everywhere

---

## 🎯 **Tracing Strategy**

### **Session 1 (15 min) - PATH 1: Main Entrance**
Trace segments 1-8 (the most important corridor)

### **Session 2 (15 min) - PATH 3: Bathrooms**
Trace segments 11-17 (high-traffic bathroom area)

### **Session 3 (10 min) - PATH 2 & Connectors**
Trace segments 9-10 and any connecting pieces

### **Session 4 (10 min) - PATH 4: Side Branch**
Trace segments 18-24 (less common but completes coverage)

---

## 📝 **Naming Convention**

Use this format when saving segments:

```
corridor_[start]_[end]

Examples:
- corridor_M1_1_M1_2
- corridor_M1_3_M1_Int_1
- corridor_M1_Turn_1_M1_8
```

---

## ✅ **After Tracing**

1. Export from Route Builder
2. Edit GeoJSON to add `startNode` and `endNode` properties
3. Save as `/map/corridor_segments_building_m.geojson`
4. System will automatically use them for ALL routes!

---

**Ready to start? Open Route Builder and begin with PATH 1!** 🚀
